-- Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS Donation;

-- Use the database
USE Donation;

-- Create the tables

-- User table
CREATE TABLE IF NOT EXISTS User (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  role VARCHAR(255) NOT NULL
);

-- Create the PhoneNumber table
CREATE TABLE PhoneNumber (
  phone_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  phonenumber VARCHAR(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Donor table
CREATE TABLE IF NOT EXISTS Donor (
  donor_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone_number VARCHAR(255) NOT NULL,
  address VARCHAR(225)
);

-- Volunteer table
CREATE TABLE IF NOT EXISTS Volunteer (
  volunteer_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone_number VARCHAR(255) NOT NULL,
  availability_start DATETIME NOT NULL,
  availability_end DATETIME NOT NULL
);

-- Create the Recipient table
CREATE TABLE Recipient (
  recipient_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  address VARCHAR(255) NOT NULL,
  category VARCHAR(255) NOT NULL
);

-- Donation table
CREATE TABLE IF NOT EXISTS Donation (
  donation_id INT AUTO_INCREMENT PRIMARY KEY,
  donation_amount DECIMAL(10, 2) NOT NULL,
  donation_date DATETIME NOT NULL,
  donor_id INT NOT NULL,
  FOREIGN KEY (donor_id) REFERENCES Donor(donor_id)
);

-- Add the "donate_to" column to the Donor table
ALTER TABLE Donor
ADD donate_to INT,
ADD FOREIGN KEY (donate_to) REFERENCES Recipient(recipient_id);

-- Add the "amount_raised" column to the Recipient table
ALTER TABLE Recipient
ADD amount_raised DECIMAL(10, 2) NOT NULL;

ALTER TABLE Recipient
ALTER COLUMN amount_raised SET DEFAULT 0;

ALTER TABLE Donor
DROP COLUMN email;

ALTER TABLE Volunteer
DROP COLUMN email;

ALTER TABLE Donation
MODIFY COLUMN donation_date datetime DEFAULT CURRENT_TIMESTAMP;

DELIMITER //

DELIMITER //

CREATE PROCEDURE InsertDonorWithDonation(
    IN p_dname VARCHAR(255),
    IN p_phno VARCHAR(255),
    IN p_daddress VARCHAR(255),
    IN p_donation_amount DECIMAL(10, 2),
    IN p_donation_date DATETIME,
    IN p_donate_to INT
)
BEGIN
    DECLARE v_donor_id INT;
    DECLARE v_recipient_amount DECIMAL(10, 2);

    -- Insert donor information
    INSERT INTO Donor (name, phone_number, address, donate_to) VALUES (p_dname, p_phno, p_daddress, p_donate_to);
    SET v_donor_id = LAST_INSERT_ID(); -- Get the last inserted donor ID

    -- Insert donation information
    INSERT INTO Donation (donation_amount, donation_date, donor_id) VALUES (p_donation_amount, p_donation_date, v_donor_id);

    -- Update recipient's amount raised
    SELECT amount_raised INTO v_recipient_amount FROM Recipient WHERE recipient_id = p_donate_to;
    UPDATE Recipient SET amount_raised = v_recipient_amount + p_donation_amount WHERE recipient_id = p_donate_to;

    COMMIT;
END //

DELIMITER ;

DELIMITER //
CREATE PROCEDURE UpdateDonor(
    IN p_donor_id INT,
    IN p_name VARCHAR(255),
    IN p_phone_number VARCHAR(255),
    IN p_address VARCHAR(255)
)
BEGIN
    UPDATE Donor
    SET name = p_name, phone_number = p_phone_number, address = p_address
    WHERE donor_id = p_donor_id;

    COMMIT;
END //
DELIMITER ;

DELIMITER //

CREATE PROCEDURE UpdateRecipient(
    IN p_recipient_id INT,
    IN p_name VARCHAR(255),
    IN p_address VARCHAR(255),
    IN p_category VARCHAR(255)
)
BEGIN
    UPDATE Recipient
    SET name = p_name, address = p_address, category = p_category
    WHERE recipient_id = p_recipient_id;
    COMMIT;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE UpdateVolunteer(
    IN p_volunteer_id INT,
    IN p_name VARCHAR(255),
    IN p_phone_number VARCHAR(255),
    IN p_availability_start DATETIME,
    IN p_availability_end DATETIME
)
BEGIN
    UPDATE Volunteer
    SET name = p_name, phone_number = p_phone_number, availability_start = p_availability_start, availability_end = p_availability_end
    WHERE volunteer_id = p_volunteer_id;
    COMMIT;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE DeleteDonorAndRelatedData(
    IN p_donor_id INT
)
BEGIN
    DELETE FROM Donation WHERE donor_id = p_donor_id;
    DELETE FROM Donor WHERE donor_id = p_donor_id;
    -- Add more delete statements for related tables if required
    -- Example: DELETE FROM PhoneNumber WHERE user_id = (SELECT user_id FROM Donor WHERE donor_id = p_donor_id);
    COMMIT;
END //
DELIMITER ;

DELIMITER //

CREATE PROCEDURE DeleteVolunteerAndRelatedData(
    IN p_volunteer_id INT
)
BEGIN
    -- Delete records from VolunteerRecipientMap
    DELETE FROM VolunteerRecipientMap WHERE volunteer_id = p_volunteer_id;

    -- Delete volunteer from the Volunteer table
    DELETE FROM Volunteer WHERE volunteer_id = p_volunteer_id;

    -- Add more delete statements for additional related tables if required

    COMMIT;
END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE DeleteRecipientAndRelatedData(
    IN p_recipient_id INT
)
BEGIN
    DECLARE v_donor_id INT;

    -- Find the donor_id associated with the recipient
    SELECT donor_id INTO v_donor_id FROM Donor WHERE donate_to = p_recipient_id;

    -- Remove references from the Donor table
    UPDATE Donor SET donate_to = NULL WHERE donate_to = p_recipient_id;

    -- Now, delete the recipient
    DELETE FROM Recipient WHERE recipient_id = p_recipient_id;

    -- If there is a donor associated with the recipient, delete the donor and related data
    IF v_donor_id IS NOT NULL THEN
        CALL DeleteDonorAndRelatedData(v_donor_id);
    END IF;

    COMMIT;
END //

DELIMITER ;

-- Create the VolunteerRecipientMap table
CREATE TABLE IF NOT EXISTS VolunteerRecipientMap (
  map_id INT AUTO_INCREMENT PRIMARY KEY,
  volunteer_id INT NOT NULL,
  recipient_id INT NOT NULL,
  CONSTRAINT fk_volunteer FOREIGN KEY (volunteer_id) REFERENCES Volunteer(volunteer_id),
  CONSTRAINT fk_recipient FOREIGN KEY (recipient_id) REFERENCES Recipient(recipient_id)
);

-- Create the trigger
DELIMITER //

CREATE TRIGGER AfterDonationInsert
AFTER INSERT
ON Donation FOR EACH ROW
BEGIN
    DECLARE v_recipient_id INT;

    -- Find the recipient_id associated with the donation
    SELECT donate_to INTO v_recipient_id FROM Donor WHERE donor_id = NEW.donor_id;

    -- Update recipient's amount raised, deducting $0.25 as tax
    UPDATE Recipient SET amount_raised = amount_raised + NEW.donation_amount - 0.25 WHERE recipient_id = v_recipient_id;
END //

DELIMITER ;








