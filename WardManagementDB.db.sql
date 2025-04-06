BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Admissions" (
	"AdmissionID"	INTEGER,
	"PatientID"	INTEGER,
	"BedID"	INTEGER,
	"AdmissionDate"	DATE NOT NULL,
	"DischargeDate"	DATE,
	"Diagnosis"	TEXT,
	"DoctorInCharge"	TEXT,
	PRIMARY KEY("AdmissionID" AUTOINCREMENT),
	FOREIGN KEY("BedID") REFERENCES "Beds"("BedID"),
	FOREIGN KEY("PatientID") REFERENCES "Patients"("PatientID")
);
CREATE TABLE IF NOT EXISTS "Beds" (
	"BedID"	INTEGER,
	"WardID"	INTEGER,
	"BedNumber"	INTEGER NOT NULL,
	"BedStatus"	TEXT CHECK("BedStatus" IN ('Occupied', 'Vacant', 'Cleaning', 'Maintenance')),
	PRIMARY KEY("BedID" AUTOINCREMENT),
	FOREIGN KEY("WardID") REFERENCES "Wards"("WardID")
);
CREATE TABLE IF NOT EXISTS "MedicalRecords" (
	"RecordID"	INTEGER,
	"PatientID"	INTEGER,
	"RecordDate"	DATE NOT NULL,
	"Allergies"	TEXT,
	"Conditions"	TEXT,
	"Medications"	TEXT,
	"Notes"	TEXT,
	PRIMARY KEY("RecordID" AUTOINCREMENT),
	FOREIGN KEY("PatientID") REFERENCES "Patients"("PatientID")
);
CREATE TABLE IF NOT EXISTS "Patients" (
	"PatientID"	INTEGER,
	"FirstName"	TEXT NOT NULL,
	"LastName"	TEXT NOT NULL,
	"DateOfBirth"	DATE NOT NULL,
	"Gender"	INTEGER CHECK("Gender" IN ('Male', 'Female', 'Other')),
	"ContactNumber"	INTEGER,
	"EmergencyContact"	INTEGER,
	"Address"	TEXT,
	PRIMARY KEY("PatientID" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Wards" (
	"WardID"	INTEGER,
	"WardName"	TEXT NOT NULL,
	"WardCapacity"	INTEGER,
	"WardType"	TEXT CHECK("WardType" IN ('General', 'Emergency', 'Intensive Care Unit', 'Intensive Coronary Care Unit', 'Nursery', 'Special Septic Nursery', 'Postoperative', 'Burn', 'Postnatal', 'Protective Isolation', 'Infectious Disease')),
	PRIMARY KEY("WardID" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "permissions" (
	"id"	INTEGER,
	"permission_name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "role_permissions" (
	"id"	INTEGER,
	"role_id"	INTEGER,
	"permission_id"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("permission_id") REFERENCES "permissions"("id"),
	FOREIGN KEY("role_id") REFERENCES "roles"("id")
);
CREATE TABLE IF NOT EXISTS "roles" (
	"id"	INTEGER,
	"role_name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"role_id"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("role_id") REFERENCES "roles"("id")
);
INSERT INTO "Admissions" VALUES (1,1,1,'2023-10-01','2023-10-05','Appendicitis','Dr. Smith');
INSERT INTO "Admissions" VALUES (2,2,2,'2023-10-02',NULL,'Pneumonia','Dr. Johnson');
INSERT INTO "Admissions" VALUES (3,3,3,'2023-10-03',NULL,'Heart Attack','Dr. Lee');
INSERT INTO "Admissions" VALUES (4,4,4,'2023-10-04','2023-10-06','Fractured Leg','Dr. Patel');
INSERT INTO "Admissions" VALUES (5,5,5,'2023-10-05',NULL,'Diabetes','Dr. Brown');
INSERT INTO "Admissions" VALUES (6,6,6,'2023-10-06','2023-10-08','Hypertension','Dr. Green');
INSERT INTO "Admissions" VALUES (7,7,7,'2023-10-07',NULL,'Asthma','Dr. White');
INSERT INTO "Admissions" VALUES (8,8,8,'2023-10-08','2023-10-10','Migraine','Dr. Black');
INSERT INTO "Admissions" VALUES (9,9,9,'2023-10-09',NULL,'Bronchitis','Dr. Gray');
INSERT INTO "Admissions" VALUES (10,10,10,'2023-10-10','2023-10-12','Arthritis','Dr. Blue');
INSERT INTO "Admissions" VALUES (11,11,11,'2023-10-11',NULL,'Flu','Dr. Red');
INSERT INTO "Admissions" VALUES (12,12,12,'2023-10-12','2023-10-14','Gastritis','Dr. Yellow');
INSERT INTO "Admissions" VALUES (13,13,13,'2023-10-13',NULL,'Sinusitis','Dr. Orange');
INSERT INTO "Admissions" VALUES (14,14,14,'2023-10-14','2023-10-16','Tonsillitis','Dr. Purple');
INSERT INTO "Admissions" VALUES (15,15,15,'2023-10-15',NULL,'Malaria','Dr. Pink');
INSERT INTO "Admissions" VALUES (16,16,16,'2023-10-16','2023-10-18','Typhoid','Dr. Cyan');
INSERT INTO "Admissions" VALUES (17,17,17,'2023-10-17',NULL,'Dengue','Dr. Magenta');
INSERT INTO "Admissions" VALUES (18,18,18,'2023-10-18','2023-10-20','Cholera','Dr. Teal');
INSERT INTO "Admissions" VALUES (19,19,19,'2023-10-19',NULL,'Tuberculosis','Dr. Maroon');
INSERT INTO "Admissions" VALUES (20,20,20,'2023-10-20','2023-10-22','COVID-19','Dr. Olive');
INSERT INTO "Beds" VALUES (1,1,101,'Occupied');
INSERT INTO "Beds" VALUES (2,1,102,'Vacant');
INSERT INTO "Beds" VALUES (3,1,103,'Cleaning');
INSERT INTO "Beds" VALUES (4,2,201,'Occupied');
INSERT INTO "Beds" VALUES (5,2,202,'Vacant');
INSERT INTO "Beds" VALUES (6,2,203,'Maintenance');
INSERT INTO "Beds" VALUES (7,3,301,'Occupied');
INSERT INTO "Beds" VALUES (8,3,302,'Vacant');
INSERT INTO "Beds" VALUES (9,3,303,'Cleaning');
INSERT INTO "Beds" VALUES (10,4,401,'Occupied');
INSERT INTO "Beds" VALUES (11,4,402,'Vacant');
INSERT INTO "Beds" VALUES (12,4,403,'Maintenance');
INSERT INTO "Beds" VALUES (13,5,501,'Occupied');
INSERT INTO "Beds" VALUES (14,5,502,'Vacant');
INSERT INTO "Beds" VALUES (15,5,503,'Cleaning');
INSERT INTO "Beds" VALUES (16,6,601,'Occupied');
INSERT INTO "Beds" VALUES (17,6,602,'Vacant');
INSERT INTO "Beds" VALUES (18,6,603,'Maintenance');
INSERT INTO "Beds" VALUES (19,7,701,'Occupied');
INSERT INTO "Beds" VALUES (20,7,702,'Vacant');
INSERT INTO "Beds" VALUES (21,7,703,'Cleaning');
INSERT INTO "Beds" VALUES (22,8,801,'Occupied');
INSERT INTO "Beds" VALUES (23,8,802,'Vacant');
INSERT INTO "Beds" VALUES (24,8,803,'Maintenance');
INSERT INTO "Beds" VALUES (25,9,901,'Occupied');
INSERT INTO "Beds" VALUES (26,9,902,'Vacant');
INSERT INTO "Beds" VALUES (27,9,903,'Cleaning');
INSERT INTO "Beds" VALUES (28,10,1001,'Occupied');
INSERT INTO "Beds" VALUES (29,10,1002,'Vacant');
INSERT INTO "Beds" VALUES (30,10,1003,'Maintenance');
INSERT INTO "Beds" VALUES (31,11,1101,'Occupied');
INSERT INTO "Beds" VALUES (32,11,1102,'Vacant');
INSERT INTO "Beds" VALUES (33,11,1103,'Cleaning');
INSERT INTO "Beds" VALUES (34,12,1201,'Occupied');
INSERT INTO "Beds" VALUES (35,12,1202,'Vacant');
INSERT INTO "Beds" VALUES (36,12,1203,'Maintenance');
INSERT INTO "Beds" VALUES (37,13,1301,'Occupied');
INSERT INTO "Beds" VALUES (38,13,1302,'Vacant');
INSERT INTO "Beds" VALUES (39,13,1303,'Cleaning');
INSERT INTO "Beds" VALUES (40,14,1401,'Occupied');
INSERT INTO "Beds" VALUES (41,14,1402,'Vacant');
INSERT INTO "Beds" VALUES (42,14,1403,'Maintenance');
INSERT INTO "Beds" VALUES (43,15,1501,'Occupied');
INSERT INTO "Beds" VALUES (44,15,1502,'Vacant');
INSERT INTO "Beds" VALUES (45,15,1503,'Cleaning');
INSERT INTO "Beds" VALUES (46,16,1601,'Occupied');
INSERT INTO "Beds" VALUES (47,16,1602,'Vacant');
INSERT INTO "Beds" VALUES (48,16,1603,'Maintenance');
INSERT INTO "Beds" VALUES (49,17,1701,'Occupied');
INSERT INTO "Beds" VALUES (50,17,1702,'Vacant');
INSERT INTO "Beds" VALUES (51,17,1703,'Cleaning');
INSERT INTO "Beds" VALUES (52,18,1801,'Occupied');
INSERT INTO "Beds" VALUES (53,18,1802,'Vacant');
INSERT INTO "Beds" VALUES (54,18,1803,'Maintenance');
INSERT INTO "Beds" VALUES (55,19,1901,'Occupied');
INSERT INTO "Beds" VALUES (56,19,1902,'Vacant');
INSERT INTO "Beds" VALUES (57,19,1903,'Cleaning');
INSERT INTO "Beds" VALUES (58,20,2001,'Occupied');
INSERT INTO "Beds" VALUES (59,20,2002,'Vacant');
INSERT INTO "Beds" VALUES (60,20,2003,'Maintenance');
INSERT INTO "MedicalRecords" VALUES (1,1,'2023-10-01','Peanuts','Hypertension','Lisinopril','Patient has a history of high blood pressure.');
INSERT INTO "MedicalRecords" VALUES (2,2,'2023-10-02','Shellfish','Diabetes','Metformin','Patient is insulin-dependent.');
INSERT INTO "MedicalRecords" VALUES (3,3,'2023-10-03','Pollen','Asthma','Albuterol','Patient uses an inhaler daily.');
INSERT INTO "MedicalRecords" VALUES (4,4,'2023-10-04','Dust','Arthritis','Ibuprofen','Patient experiences joint pain.');
INSERT INTO "MedicalRecords" VALUES (5,5,'2023-10-05','None','Migraine','Sumatriptan','Patient has frequent migraines.');
INSERT INTO "MedicalRecords" VALUES (6,6,'2023-10-06','Penicillin','Bronchitis','Amoxicillin','Patient has a persistent cough.');
INSERT INTO "MedicalRecords" VALUES (7,7,'2023-10-07','None','Gastritis','Omeprazole','Patient experiences stomach pain.');
INSERT INTO "MedicalRecords" VALUES (8,8,'2023-10-08','Latex','Sinusitis','Cetirizine','Patient has chronic sinus issues.');
INSERT INTO "MedicalRecords" VALUES (9,9,'2023-10-09','None','Tonsillitis','Penicillin','Patient has a sore throat.');
INSERT INTO "MedicalRecords" VALUES (10,10,'2023-10-10','Eggs','Malaria','Chloroquine','Patient recently traveled to a malaria-endemic area.');
INSERT INTO "MedicalRecords" VALUES (11,11,'2023-10-11','None','Typhoid','Ciprofloxacin','Patient has a high fever.');
INSERT INTO "MedicalRecords" VALUES (12,12,'2023-10-12','Soy','Dengue','Paracetamol','Patient has low platelet count.');
INSERT INTO "MedicalRecords" VALUES (13,13,'2023-10-13','None','Cholera','Doxycycline','Patient has severe dehydration.');
INSERT INTO "MedicalRecords" VALUES (14,14,'2023-10-14','Nuts','Tuberculosis','Rifampin','Patient is undergoing TB treatment.');
INSERT INTO "MedicalRecords" VALUES (15,15,'2023-10-15','None','COVID-19','Remdesivir','Patient is in isolation.');
INSERT INTO "MedicalRecords" VALUES (16,16,'2023-10-16','None','Appendicitis','Cefazolin','Patient underwent surgery.');
INSERT INTO "MedicalRecords" VALUES (17,17,'2023-10-17','None','Pneumonia','Azithromycin','Patient has difficulty breathing.');
INSERT INTO "MedicalRecords" VALUES (18,18,'2023-10-18','None','Heart Attack','Aspirin','Patient is in critical condition.');
INSERT INTO "MedicalRecords" VALUES (19,19,'2023-10-19','None','Fractured Leg','Acetaminophen','Patient is in a cast.');
INSERT INTO "MedicalRecords" VALUES (20,20,'2023-10-20','None','Flu','Oseltamivir','Patient has a fever, cough and body ache.');
INSERT INTO "Patients" VALUES (1,'John','Doe','1985-05-15','Male',1234567890,9876543210,'123 Main St, CityA');
INSERT INTO "Patients" VALUES (2,'Jane','Smith','1990-08-22','Female',2345678901,8765432109,'456 Elm St, CityB');
INSERT INTO "Patients" VALUES (3,'Alice','Johnson','1978-12-10','Female',3456789012,7654321098,'789 Oak St, CityC');
INSERT INTO "Patients" VALUES (4,'Bob','Brown','1995-03-25','Male',4567890123,6543210987,'101 Pine St, CityD');
INSERT INTO "Patients" VALUES (5,'Charlie','Davis','1982-07-30','Male',5678901234,5432109876,'202 Maple St, CityE');
INSERT INTO "Patients" VALUES (6,'Diana','Evans','1992-11-05','Female',6789012345,4321098765,'303 Birch St, CityF');
INSERT INTO "Patients" VALUES (7,'Ethan','Green','1988-04-12','Male',7890123456,3210987654,'404 Cedar St, CityG');
INSERT INTO "Patients" VALUES (8,'Fiona','Harris','1975-09-18','Female',8901234567,2109876543,'505 Walnut St, CityH');
INSERT INTO "Patients" VALUES (9,'George','Clark','1998-01-20','Male',9012345678,1098765432,'606 Spruce St, CityI');
INSERT INTO "Patients" VALUES (10,'Hannah','Lewis','1980-06-14','Female',1234509876,9876543210,'707 Fir St, CityJ');
INSERT INTO "Patients" VALUES (11,'Ian','Walker','1993-02-28','Male',2345610987,8765432109,'808 Ash St, CityK');
INSERT INTO "Patients" VALUES (12,'Julia','Hall','1987-10-03','Female',3456721098,7654321098,'909 Beech St, CityL');
INSERT INTO "Patients" VALUES (13,'Kevin','Allen','1970-12-25','Male',4567832109,6543210987,'111 Cherry St, CityM');
INSERT INTO "Patients" VALUES (14,'Laura','Young','1996-08-07','Female',5678943210,5432109876,'222 Dogwood St, CityN');
INSERT INTO "Patients" VALUES (15,'Michael','King','1983-03-19','Male',6789054321,4321098765,'333 Elm St, CityO');
INSERT INTO "Patients" VALUES (16,'Nora','Wright','1972-07-22','Female',7890165432,3210987654,'444 Fir St, CityP');
INSERT INTO "Patients" VALUES (17,'Oscar','Scott','1991-05-30','Male',8901276543,2109876543,'555 Grove St, CityQ');
INSERT INTO "Patients" VALUES (18,'Penny','Adams','1989-11-12','Female',9012387654,1098765432,'666 Hill St, CityR');
INSERT INTO "Patients" VALUES (19,'Quincy','Nelson','1977-04-05','Male',1234598765,9876543210,'777 Lake St, CityS');
INSERT INTO "Patients" VALUES (20,'Rachel','Carter','1994-09-09','Female',2345609876,8765432109,'888 Park St, CityT');
INSERT INTO "Wards" VALUES (1,'General Ward A',20,'General');
INSERT INTO "Wards" VALUES (2,'General Ward B',15,'General');
INSERT INTO "Wards" VALUES (3,'Emergency Ward A',10,'Emergency');
INSERT INTO "Wards" VALUES (4,'Emergency Ward B',12,'Emergency');
INSERT INTO "Wards" VALUES (5,'Intensive Care Unit A',5,'Intensive Care Unit');
INSERT INTO "Wards" VALUES (6,'Intensive Care Unit B',6,'Intensive Care Unit');
INSERT INTO "Wards" VALUES (7,'Intensive Coronary Care Unit A',4,'Intensive Coronary Care Unit');
INSERT INTO "Wards" VALUES (8,'Intensive Coronary Care Unit B',5,'Intensive Coronary Care Unit');
INSERT INTO "Wards" VALUES (9,'Nursery A',8,'Nursery');
INSERT INTO "Wards" VALUES (10,'Nursery B',10,'Nursery');
INSERT INTO "Wards" VALUES (11,'Special Septic Nursery A',6,'Special Septic Nursery');
INSERT INTO "Wards" VALUES (12,'Special Septic Nursery B',7,'Special Septic Nursery');
INSERT INTO "Wards" VALUES (13,'Postoperative Ward A',12,'Postoperative');
INSERT INTO "Wards" VALUES (14,'Postoperative Ward B',14,'Postoperative');
INSERT INTO "Wards" VALUES (15,'Burn Ward A',5,'Burn');
INSERT INTO "Wards" VALUES (16,'Burn Ward B',6,'Burn');
INSERT INTO "Wards" VALUES (17,'Postnatal Ward A',8,'Postnatal');
INSERT INTO "Wards" VALUES (18,'Postnatal Ward B',10,'Postnatal');
INSERT INTO "Wards" VALUES (19,'Infectious Disease Ward A',6,'Infectious Disease');
INSERT INTO "Wards" VALUES (20,'Infectious Disease Ward B',7,'Infectious Disease');
INSERT INTO "permissions" VALUES (1,'add_patient');
INSERT INTO "permissions" VALUES (2,'discharge_patient');
INSERT INTO "permissions" VALUES (3,'view_patients');
INSERT INTO "permissions" VALUES (4,'manage_users');
INSERT INTO "permissions" VALUES (5,'assign_bed');
INSERT INTO "permissions" VALUES (6,'update_medical_records');
INSERT INTO "permissions" VALUES (7,'view_medical_records');
INSERT INTO "role_permissions" VALUES (1,1,1);
INSERT INTO "role_permissions" VALUES (2,1,2);
INSERT INTO "role_permissions" VALUES (3,1,3);
INSERT INTO "role_permissions" VALUES (4,1,4);
INSERT INTO "role_permissions" VALUES (5,1,5);
INSERT INTO "role_permissions" VALUES (6,1,6);
INSERT INTO "role_permissions" VALUES (7,1,7);
INSERT INTO "role_permissions" VALUES (8,2,1);
INSERT INTO "role_permissions" VALUES (9,2,2);
INSERT INTO "role_permissions" VALUES (10,2,3);
INSERT INTO "role_permissions" VALUES (11,2,6);
INSERT INTO "role_permissions" VALUES (12,2,7);
INSERT INTO "role_permissions" VALUES (13,3,1);
INSERT INTO "role_permissions" VALUES (14,3,3);
INSERT INTO "role_permissions" VALUES (15,3,7);
INSERT INTO "roles" VALUES (1,'Admin');
INSERT INTO "roles" VALUES (2,'Doctor');
INSERT INTO "roles" VALUES (3,'Nurse');
INSERT INTO "users" VALUES (1,'admin1','scrypt:32768:8:1$N0i5pMuQSTazq94r$71191f4d17aea1ec542cca9f55419350b9ac113303a8875cb3adbc9f72f18ace8ad34606c44fec0164fce02088226cef8783da261432c8c953e8d96ca94dcd8d',1);
INSERT INTO "users" VALUES (2,'doctor1','scrypt:32768:8:1$cMWnn2EPnLAr7ss6$c9ca64867b2bd29e96a12e42fc622060c092b9f74eb29639d52d4907a87d9746cbb46f50bdedf6b71f29fabcec0cc5a627d46dfd8859567275e3408c374b3b47',2);
INSERT INTO "users" VALUES (3,'nurse1','scrypt:32768:8:1$Y4rC1omHPklSevUI$efe1ea2c461732e93e85867dc37629fe77058a2179623a89556ac3753a5c49c422b691261338c5d621f73df1a651095b5e2a8c1c50cb7ece7d8df3cb1dff9374',3);
CREATE UNIQUE INDEX IF NOT EXISTS "idx_role_permission" ON "role_permissions" (
	"role_id",
	"permission_id"
);
COMMIT;
