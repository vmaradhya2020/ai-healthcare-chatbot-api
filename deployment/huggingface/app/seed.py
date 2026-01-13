"""
Seed database with default test data for deployment
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, Base, engine
from app import models
from app.auth import get_password_hash
from app.config import settings

logger = logging.getLogger(__name__)


def seed_database():
    """Seed database with test data if SEED_DATA environment variable is set"""

    if not settings.SEED_DATA:
        logger.info("SEED_DATA not enabled, skipping database seeding")
        return

    logger.info("Starting database seeding...")
    db = SessionLocal()

    try:
        # Check if admin user already exists
        existing_admin = db.query(models.User).filter(
            models.User.email == "admin@cityhospital.com"
        ).first()

        if existing_admin:
            logger.info("Admin user already exists, skipping seed")
            return

        # Create sample clients
        logger.info("Creating clients...")
        clients_data = [
            {
                "name": "City General Hospital",
                "client_code": "CITY001",
                "address": "123 Medical Plaza, Healthcare District, NY 10001"
            },
            {
                "name": "St. Mary's Medical Center",
                "client_code": "MARY002",
                "address": "456 Health Avenue, Medical City, CA 90210"
            },
            {
                "name": "Community Health Clinic",
                "client_code": "COMM003",
                "address": "789 Wellness Street, Care Town, TX 75001"
            },
            {
                "name": "Advanced Diagnostics Center",
                "client_code": "DIAG004",
                "address": "321 Innovation Drive, Tech Med Park, MA 02101"
            }
        ]

        clients = []
        for client_data in clients_data:
            # Check if client already exists
            existing = db.query(models.Client).filter(
                models.Client.client_code == client_data["client_code"]
            ).first()

            if not existing:
                client = models.Client(**client_data)
                db.add(client)
                clients.append(client)
            else:
                clients.append(existing)

        db.commit()
        logger.info(f"Created {len([c for c in clients if c.id])} clients")

        # Create default admin user
        logger.info("Creating admin user...")
        admin_user = models.User(
            email="admin@cityhospital.com",
            password_hash=get_password_hash("password123")
        )
        db.add(admin_user)
        db.commit()
        logger.info("Admin user created successfully")

        # Link admin to first client
        if clients:
            user_client = models.UserClient(
                user_id=admin_user.id,
                client_id=clients[0].id,
                is_primary=1
            )
            db.add(user_client)
            db.commit()
            logger.info("Admin user linked to client")

        # Create sample equipment for City General Hospital
        logger.info("Creating sample equipment...")
        equipment_data = [
            {
                "client_id": clients[0].id,
                "model_name": "Ultrasound Machine Pro 5000",
                "serial_number": "USM-2023-001",
                "category": "ultrasound",
                "purchase_date": datetime.now() - timedelta(days=365),
                "status": "active"
            },
            {
                "client_id": clients[0].id,
                "model_name": "Digital X-Ray System DXR-3000",
                "serial_number": "XRY-2023-002",
                "category": "xray",
                "purchase_date": datetime.now() - timedelta(days=300),
                "status": "active"
            },
            {
                "client_id": clients[0].id,
                "model_name": "Patient Monitor Elite 600",
                "serial_number": "MON-2023-003",
                "category": "monitoring",
                "purchase_date": datetime.now() - timedelta(days=200),
                "status": "active"
            }
        ]

        equipment_list = []
        for eq_data in equipment_data:
            equipment = models.Equipment(**eq_data)
            db.add(equipment)
            equipment_list.append(equipment)

        db.commit()
        logger.info(f"Created {len(equipment_list)} equipment items")

        # Create sample order
        logger.info("Creating sample order...")
        order = models.Order(
            client_id=clients[0].id,
            equipment_id=equipment_list[0].id,
            tracking_number="TRK-2023-1000",
            order_date=datetime.now() - timedelta(days=30),
            expected_delivery_date=datetime.now() - timedelta(days=10),
            status="delivered"
        )
        db.add(order)
        db.commit()
        logger.info("Sample order created")

        # Create sample invoice
        logger.info("Creating sample invoice...")
        invoice = models.Invoice(
            client_id=clients[0].id,
            amount=125000.00,
            currency="USD",
            invoice_date=datetime.now() - timedelta(days=25),
            due_date=datetime.now() + timedelta(days=5),
            status="pending"
        )
        db.add(invoice)
        db.commit()
        logger.info("Sample invoice created")

        # Create sample warranty
        logger.info("Creating sample warranty...")
        warranty = models.Warranty(
            equipment_id=equipment_list[0].id,
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now() + timedelta(days=365),
            coverage_details="Full parts and labor coverage for 2 years",
            status="active"
        )
        db.add(warranty)
        db.commit()
        logger.info("Sample warranty created")

        # Create sample AMC contract
        logger.info("Creating sample AMC contract...")
        amc = models.AMCContract(
            equipment_id=equipment_list[1].id,
            start_date=datetime.now() - timedelta(days=180),
            end_date=datetime.now() + timedelta(days=185),
            cost=15000.00,
            sla_details="Preventive maintenance every 3 months with emergency support",
            status="active"
        )
        db.add(amc)
        db.commit()
        logger.info("Sample AMC contract created")

        logger.info("="*80)
        logger.info("Database seeding completed successfully!")
        logger.info("="*80)
        logger.info("Test Credentials:")
        logger.info("  Email: admin@cityhospital.com")
        logger.info("  Password: password123")
        logger.info("="*80)

    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Some data already exists (IntegrityError): {e}")
        logger.info("Continuing with existing data...")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}", exc_info=True)
        logger.warning("Seed failed but application will continue. You can seed manually later.")
        # Don't raise - let the application start even if seeding fails

    finally:
        db.close()


if __name__ == "__main__":
    # Can be run directly: python -m app.seed
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    seed_database()
