from app.models.user import User
from app.models.goal import GoalSheet, Goal
from app.models.cycle import Cycle
from app.models.department import Department
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.database import SessionLocal, engine, Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def clean_and_seed():
    """Wipe database schema and seed initial test accounts, departments, and goal sheets for testing."""
    print("Cleaning database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database wiped clean and recreated!")

    db = SessionLocal()
    try:
        print("\nSeeding Flow...")

        # 0. Setup Departments
        ops_dept = Department(name="Operations", is_active=True)
        eng_dept = Department(name="Engineering", is_active=True)
        db.add_all([ops_dept, eng_dept])
        db.commit()
        db.refresh(ops_dept)
        db.refresh(eng_dept)
        print("✓ Created Departments: Operations, Engineering")

        # 1. Setup Admin
        admin = User(
            email="admin@atomquest.com",
            full_name="System Admin",
            hashed_password=pwd_context.hash("password"),
            role="admin",
            department_id=ops_dept.id,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("✓ Created Admin: admin@atomquest.com")

        # 2. Setup Cycle
        now = datetime.now(timezone.utc)
        cycle = Cycle(
            name="2026 Annual Cycle",
            goal_setting_open=now - timedelta(days=10),
            q1_open=now + timedelta(days=80),
            q2_open=now + timedelta(days=170),
            q3_open=now + timedelta(days=260),
            q4_open=now + timedelta(days=350),
            is_active=True,
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        print(f"✓ Created Active Cycle: {cycle.name}")

        # 3. Setup Hierarchy (Director -> Manager -> Employee)
        director = User(
            email="director@atomquest.com",
            full_name="Diana Director",
            hashed_password=pwd_context.hash("password"),
            role="manager",
            department_id=eng_dept.id,
            is_active=True,
        )
        db.add(director)
        db.commit()
        db.refresh(director)

        manager = User(
            email="manager@atomquest.com",
            full_name="Michael Manager",
            hashed_password=pwd_context.hash("password"),
            role="manager",
            department_id=eng_dept.id,
            manager_id=director.id,
            is_active=True,
        )
        db.add(manager)
        db.commit()
        db.refresh(manager)
        print("✓ Created Manager: manager@atomquest.com")

        employee = User(
            email="employee@atomquest.com",
            full_name="Evan Employee",
            hashed_password=pwd_context.hash("password"),
            role="employee",
            department_id=eng_dept.id,
            manager_id=manager.id,
            is_active=True,
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        print("✓ Created Employee: employee@atomquest.com")

        # 4. Setup Employee's Goal Sheet (Draft Status)
        sheet = GoalSheet(
            employee_id=employee.id,
            cycle_id=cycle.id,
            status="draft",
            total_weightage=0,
        )
        db.add(sheet)
        db.commit()
        db.refresh(sheet)
        print("✓ Created Draft Goal Sheet for Employee")

        # 5. Add Goals summing up to 100%
        g1 = Goal(
            goal_sheet_id=sheet.id,
            title="Complete Frontend Refactor",
            description="Migrate all legacy CSS to Tailwind classes.",
            thrust_area="Technical Debt",
            uom_type="min",
            target_value=100,
            weightage=40,
        )
        g2 = Goal(
            goal_sheet_id=sheet.id,
            title="Resolve 20 Jira Tickets",
            description="Close out high-priority customer bugs.",
            thrust_area="Customer Success",
            uom_type="max",
            target_value=20,
            weightage=30,
        )
        g3 = Goal(
            goal_sheet_id=sheet.id,
            title="Launch Feature X",
            description="Deliver the new feature by Q2.",
            thrust_area="Product",
            uom_type="timeline",
            target_date=now + timedelta(days=90),
            weightage=30,
        )
        db.add_all([g1, g2, g3])
        sheet.total_weightage = 100
        db.commit()
        print("✓ Populated Goal Sheet with 3 goals (Totaling 100%)")

        print("\n--------------------------------------------------")
        print("RE-SEED COMPLETED SUCCESSFULLY!")
        print("All passwords are set to: password")
        print("Log in as employee@atomquest.com to test the Submit flow.")
        print("Then log in as manager@atomquest.com to test the Approval flow.")
        print("--------------------------------------------------")

    except Exception as e:
        print("Error during seeding:", e)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    clean_and_seed()
