from sqlmodel import Session, select

from database import engine
from models.skill import Skill

_BUILTINS = [
    {
        "name": "add-tests",
        "description": "Generate a complete test suite for all untested functions.",
        "system_prompt_addition": "Generate a complete test suite for all untested functions. Match the existing test framework and fixtures pattern.",
    },
    {
        "name": "add-openapi-docs",
        "description": "Add OpenAPI/Swagger docstrings to all route handlers.",
        "system_prompt_addition": "Add OpenAPI/Swagger docstrings to all route handlers. Follow the existing documentation style.",
    },
    {
        "name": "dependency-audit",
        "description": "Identify all outdated or vulnerable dependencies. Update them and fix any breaking changes.",
        "system_prompt_addition": "Identify all outdated or vulnerable dependencies. Update them and fix any breaking changes.",
    },
    {
        "name": "add-logging",
        "description": "Add structured logging to all service functions.",
        "system_prompt_addition": "Add structured logging to all service functions using the existing logger configuration.",
    },
    {
        "name": "add-error-handling",
        "description": "Wrap all service calls in proper error handling with typed exceptions.",
        "system_prompt_addition": "Wrap all service calls in proper error handling with typed exceptions matching the existing error patterns.",
    },
]


class SkillsService:
    def get_skill(self, name: str, api_key_id: str) -> Skill | None:
        with Session(engine) as session:
            user_skill = session.exec(
                select(Skill).where(Skill.name == name, Skill.owner_key_id == api_key_id)
            ).first()
            if user_skill:
                return user_skill
            return session.exec(
                select(Skill).where(Skill.name == name, Skill.owner_key_id.is_(None))
            ).first()

    def list_skills(self, api_key_id: str) -> list[Skill]:
        with Session(engine) as session:
            builtins = list(session.exec(
                select(Skill).where(Skill.owner_key_id.is_(None))
            ).all())
            user_skills = list(session.exec(
                select(Skill).where(Skill.owner_key_id == api_key_id)
            ).all())
            return builtins + user_skills

    def create_skill(self, api_key_id: str, name: str, description: str, system_prompt_addition: str) -> Skill:
        skill = Skill(
            name=name,
            owner_key_id=api_key_id,
            description=description,
            system_prompt_addition=system_prompt_addition,
        )
        with Session(engine) as session:
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill

    def delete_skill(self, skill_id: str, api_key_id: str) -> bool:
        with Session(engine) as session:
            skill = session.get(Skill, skill_id)
            if not skill or skill.owner_key_id != api_key_id:
                return False
            session.delete(skill)
            session.commit()
            return True

    def seed_builtins(self) -> None:
        try:
            with Session(engine) as session:
                for b in _BUILTINS:
                    existing = session.exec(
                        select(Skill).where(Skill.name == b["name"], Skill.owner_key_id.is_(None))
                    ).first()
                    if not existing:
                        session.add(Skill(
                            name=b["name"],
                            owner_key_id=None,
                            description=b["description"],
                            system_prompt_addition=b["system_prompt_addition"],
                        ))
                session.commit()
        except Exception as e:
            print(f"Warning: seed_builtins failed (schema migration needed): {e}")
            return


def migrate_skills_table():
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            new_columns = [
                ("is_public", "BOOLEAN DEFAULT FALSE"),
                ("author_id", "VARCHAR"),
                ("author_username", "VARCHAR"),
                ("tags", "VARCHAR"),
                ("install_count", "INTEGER DEFAULT 0"),
                ("star_count", "INTEGER DEFAULT 0"),
                ("version", "VARCHAR DEFAULT '1.0.0'"),
            ]
            for col_name, col_def in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE skill ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    print(f"Migrated: added column {col_name} to skill table")
                except Exception:
                    pass
    except Exception as e:
        print(f"Warning: skills table migration failed: {e}")
