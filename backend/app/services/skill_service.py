import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from git import Repo
from git.exc import GitCommandError
from datetime import datetime

from app.core.config import get_settings
from app.schemas import SkillScope

settings = get_settings()


def compute_folder_hash(folder_path: Path) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(folder_path.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(folder_path)
            hasher.update(str(rel_path).encode())
            hasher.update(b"\x00")
            hasher.update(file_path.read_bytes())
            hasher.update(b"\x00")
    return hasher.hexdigest()


def parse_skill_md(skill_md_path: Path) -> dict:
    import frontmatter
    post = frontmatter.load(skill_md_path)
    return {
        "name": post.get("name", ""),
        "description": post.get("description", ""),
        "version": post.get("version", "1.0.0"),
        "author": post.get("author", ""),
        "tags": post.get("tags", []),
        "content": post.content,
    }


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token

    def _get_clone_url(self, repo_url: str) -> str:
        if self.token and "github.com" in repo_url:
            return repo_url.replace("https://", f"https://oauth2:{self.token}@")
        return repo_url

    async def sparse_clone_skill(
        self,
        repo_url: str,
        skill_path: str,
        target_dir: Path,
        branch: str = "main",
        depth: int = 1,
    ) -> tuple[Path, str]:
        target_dir.mkdir(parents=True, exist_ok=True)

        clone_url = self._get_clone_url(repo_url)
        repo_dir = target_dir / ".git_repo"

        try:
            repo = Repo.init(repo_dir)
            origin = repo.create_remote("origin", clone_url)

            repo.git.config("core.sparseCheckout", "true")
            sparse_checkout_file = repo_dir / ".git" / "info" / "sparse-checkout"
            sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
            sparse_checkout_file.write_text(f"{skill_path}/*\n")

            origin.fetch(refspec=branch, depth=depth)
            repo.git.checkout(f"origin/{branch}")

            skill_dir = repo_dir / skill_path
            if not skill_dir.exists():
                raise FileNotFoundError(f"Skill path not found: {skill_path}")

            final_dir = target_dir / "skill"
            if final_dir.exists():
                shutil.rmtree(final_dir)
            shutil.copytree(skill_dir, final_dir)

            folder_hash = compute_folder_hash(final_dir)
            return final_dir, folder_hash

        except GitCommandError as e:
            raise RuntimeError(f"Git operation failed: {e}")
        finally:
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)

    async def get_default_branch(self, repo_url: str) -> str:
        return "main"

    async def get_latest_commit_hash(self, repo_url: str, branch: str = "main") -> str:
        return ""


class SkillService:
    def __init__(self, db, github_service: GitHubService):
        self.db = db
        self.github = github_service

    async def install_skill(
        self,
        user_id,
        source_url: str,
        skill_name: str,
        skill_path: Optional[str],
        scope: SkillScope,
        force: bool = False,
    ):
        from app.models import Skill, SkillStatus, LockFile
        from sqlalchemy import select

        existing = await self.db.execute(
            select(Skill).where(
                Skill.owner_id == user_id,
                Skill.name == skill_name,
                Skill.scope == scope,
            )
        )
        existing_skill = existing.scalar_one_or_none()

        if existing_skill and not force:
            raise ValueError(f"Skill '{skill_name}' already installed. Use --force to reinstall.")

        if not skill_path:
            skill_path = f"skills/{skill_name}"

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            skill_dir, folder_hash = await self.github.sparse_clone_skill(
                source_url, skill_path, target_dir
            )

            skill_md_path = skill_dir / "SKILL.md"
            skill_metadata = {}
            if skill_md_path.exists():
                skill_metadata = parse_skill_md(skill_md_path)

            target_base = Path.home() / ".agents" / "skills" if scope == SkillScope.GLOBAL else Path.cwd() / ".agents" / "skills"
            target_path = target_base / skill_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(skill_dir, target_path)

        if existing_skill:
            existing_skill.source_url = source_url
            existing_skill.source_type = "github"
            existing_skill.skill_path = skill_path
            existing_skill.skill_folder_hash = folder_hash
            existing_skill.scope = scope
            existing_skill.status = SkillStatus.INSTALLED
            existing_skill.target_path = str(target_path)
            existing_skill.skill_metadata = json.dumps(skill_metadata)
            existing_skill.installed_at = datetime.utcnow()
            skill = existing_skill
        else:
            skill = Skill(
                owner_id=user_id,
                name=skill_name,
                source_url=source_url,
                source_type="github",
                skill_path=skill_path,
                skill_folder_hash=folder_hash,
                scope=scope,
                status=SkillStatus.INSTALLED,
                target_path=str(target_path),
                skill_metadata=json.dumps(skill_metadata),
                installed_at=datetime.utcnow(),
            )
            self.db.add(skill)

        await self.db.flush()
        await self._update_lock_file(user_id, scope)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill, True

    async def _update_lock_file(self, user_id, scope: SkillScope):
        from app.models import Skill, LockFile
        from sqlalchemy import select

        skills = await self.db.execute(
            select(Skill).where(
                Skill.owner_id == user_id,
                Skill.scope == scope,
                Skill.status == SkillStatus.INSTALLED,
            )
        )

        lock_data = {
            "version": 3,
            "skills": {},
            "dismissed": {"findSkillsPrompt": True},
        }

        for skill in skills.scalars().all():
            lock_data["skills"][skill.name] = {
                "source": skill.source_url.split("/")[-2] + "/" + skill.source_url.split("/")[-1].replace(".git", ""),
                "sourceType": skill.source_type,
                "sourceUrl": skill.source_url,
                "skillPath": skill.skill_path,
                "skillFolderHash": skill.skill_folder_hash,
                "installedAt": skill.installed_at.isoformat() + "Z" if skill.installed_at else "",
                "updatedAt": skill.updated_at.isoformat() + "Z" if skill.updated_at else "",
            }

        lock_file = await self.db.execute(
            select(LockFile).where(
                LockFile.owner_id == user_id,
                LockFile.scope == scope,
            )
        )
        lock_file = lock_file.scalar_one_or_none()

        if lock_file:
            lock_file.content = json.dumps(lock_data, indent=2)
            lock_file.version = "3"
        else:
            lock_file = LockFile(
                owner_id=user_id,
                scope=scope,
                content=json.dumps(lock_data, indent=2),
                version="3",
            )
            self.db.add(lock_file)

    async def install_from_lock(
        self,
        user_id,
        scope: SkillScope,
        force: bool = False,
    ):
        from app.models import LockFile, Skill, SkillStatus
        from sqlalchemy import select

        lock_file = await self.db.execute(
            select(LockFile).where(
                LockFile.owner_id == user_id,
                LockFile.scope == scope,
            )
        )
        lock_file = lock_file.scalar_one_or_none()

        if not lock_file:
            raise ValueError("No lock file found for this scope")

        lock_data = json.loads(lock_file.content)
        results = []

        for skill_name, skill_data in lock_data.get("skills", {}).items():
            try:
                skill, _ = await self.install_skill(
                    user_id=user_id,
                    source_url=skill_data["sourceUrl"],
                    skill_name=skill_name,
                    skill_path=skill_data.get("skillPath"),
                    scope=scope,
                    force=force,
                )
                results.append({"name": skill_name, "status": "installed"})
            except Exception as e:
                results.append({"name": skill_name, "status": "failed", "error": str(e)})

        return results

    async def check_updates(self, user_id, scope: SkillScope):
        from app.models import Skill, SkillStatus
        from sqlalchemy import select

        skills = await self.db.execute(
            select(Skill).where(
                Skill.owner_id == user_id,
                Skill.scope == scope,
                Skill.status == SkillStatus.INSTALLED,
            )
        )

        updates = []
        for skill in skills.scalars().all():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_dir = Path(tmpdir)
                try:
                    skill_dir, new_hash = await self.github.sparse_clone_skill(
                        skill.source_url, skill.skill_path, target_dir
                    )
                    if new_hash != skill.skill_folder_hash:
                        updates.append({
                            "skill_id": str(skill.id),
                            "name": skill.name,
                            "current_hash": skill.skill_folder_hash,
                            "new_hash": new_hash,
                        })
                except Exception:
                    pass

        return updates

    async def update_skill(self, user_id, skill_id, force: bool = False):
        from app.models import Skill, SkillStatus
        from sqlalchemy import select

        skill = await self.db.execute(
            select(Skill).where(
                Skill.id == skill_id,
                Skill.owner_id == user_id,
            )
        )
        skill = skill.scalar_one_or_none()

        if not skill:
            raise ValueError("Skill not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            skill_dir, new_hash = await self.github.sparse_clone_skill(
                skill.source_url, skill.skill_path, target_dir
            )

            if new_hash == skill.skill_folder_hash and not force:
                return {"status": "up_to_date", "skill": skill}

            skill_md_path = skill_dir / "SKILL.md"
            skill_metadata = {}
            if skill_md_path.exists():
                skill_metadata = parse_skill_md(skill_md_path)

            target_path = Path(skill.target_path)
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(skill_dir, target_path)

            skill.skill_folder_hash = new_hash
            skill.status = SkillStatus.INSTALLED
            skill.skill_metadata = json.dumps(skill_metadata)
            skill.updated_at = datetime.utcnow()

        await self._update_lock_file(user_id, skill.scope)
        await self.db.commit()
        await self.db.refresh(skill)

        return {"status": "updated", "skill": skill}