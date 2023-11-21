import streamlit as st
import mysql.connector
import datetime
import pandas as pd

# Function to establish a database connection
def get_database_connection():
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "password",
        "database": "Donation"
    }
    conn = mysql.connector.connect(**db_config)

    return conn

def display_donor_table():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Use a nested query to get aggregated data
    query = """
        SELECT d.*, COALESCE(SUM(Donation.donation_amount), 0) AS total_donation
        FROM Donor d
        LEFT JOIN Donation ON d.donor_id = Donation.donor_id
        GROUP BY d.donor_id, d.name, d.phone_number, d.address, d.donate_to
    """
    cursor.execute(query)
    donors = cursor.fetchall()
    cursor.close()
    conn.close()

    if donors:
        st.write("Donors:")
        donor_data = []
        for donor in donors:
            donor_data.append([donor[0], donor[1], donor[2], donor[3], donor[4], donor[5]])
        donor_df = pd.DataFrame(donor_data, columns=["Donor ID", "Name", "Phone Number", "Address", "Donate To", "Total Donation"])
        st.table(donor_df)


# Function to display volunteer table
def display_volunteer_table():
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Volunteer")
    volunteers = cursor.fetchall()
    cursor.close()
    conn.close()

    if volunteers:
        st.write("Volunteers:")
        volunteer_data = []
        columns = len(volunteers[0]) if volunteers else 0
        for volunteer in volunteers:
            volunteer_data.append(volunteer[:columns])
        volunteer_df = pd.DataFrame(volunteer_data, columns=["Volunteer ID", "Name", "Phone Number", "Available from", "Available Till"])
        st.table(volunteer_df)

def display_recipient_table():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Use a nested query to get aggregated data
    query = """
        SELECT r.*, COALESCE(SUM(Donation.donation_amount), 0) AS amount_raised
        FROM Recipient r
        LEFT JOIN Donor ON r.recipient_id = Donor.donate_to
        LEFT JOIN Donation ON Donor.donor_id = Donation.donor_id
        GROUP BY r.recipient_id, r.name, r.address, r.category
    """
    cursor.execute(query)
    recipients = cursor.fetchall()
    cursor.close()
    conn.close()

    if recipients:
        st.write("Recipients:")
        recipient_data = []
        for recipient in recipients:
            recipient_data.append([recipient[0], recipient[1], recipient[2], recipient[3], recipient[4]])
        recipient_df = pd.DataFrame(recipient_data, columns=["Recipient ID", "Name", "Address", "Category", "Amount Raised"])
        st.table(recipient_df)


# Function to insert donor with donation
def insert_donor_with_donation(dname, phno, daddress, donation_amount, donate_to):
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        cursor.callproc('InsertDonorWithDonation', (dname, phno, daddress, donation_amount, datetime.datetime.now(), donate_to))
        st.success("Donor and donation information submitted successfully!")
    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Streamlit app layout
st.set_page_config(layout="wide")
st.title("CharityHUB")

# User registration form
st.subheader("Create an Account")
user_data = {"username": st.text_input("Username"), "email": st.text_input("Email"), "password": st.text_input("Password", type="password"), "role": st.selectbox("Choose Role: ", ['Donor', 'Volunteer', 'Recipient'])}

# Print the selected role
st.write("You will register as a:", user_data["role"])

# Sign Up button
if st.button("Sign Up"):
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        insert_query = "INSERT INTO User (username, email, password, role) VALUES (%s, %s, %s, %s)"
        user_values = (user_data["username"], user_data["email"], user_data["password"], user_data["role"])
        cursor.execute(insert_query, user_values)
        conn.commit()
        st.success("Account created successfully!")
    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Select Operation (Create, Read, Update, Delete)
section = st.sidebar.selectbox("Select Operation", ["Create", "Read", "Update", "Delete"])

# Sections for different roles
if section == "Create":
    if user_data["role"] == 'Donor':
        st.subheader("Donor Information")
        donor_data = {"dname": "", "phno": "", "daddress": "", "donation_amount": 0.0, "donation_date": None, "donate_to": None}

        # Display the Recipient Table
        
        donor_data["dname"] = st.text_input("Enter Name:")
        donor_data["phno"] = st.text_input("Enter Phone number:")
        donor_data["daddress"] = st.text_input("Enter Address:")
        st.subheader("Select Recipient for Donation")
        recipients = display_recipient_table()  # You should define a function to read recipient
        # You can use the selected recipient ID here in donor_data["donate_to"]
        donor_data["donate_to"] = st.text_input("Enter Recipient ID to donate to:")
        donor_data["donation_amount"] = st.number_input("Enter Donation Amount (in USD)", min_value=0.0)
        donor_data["donation_date"] = datetime.date.today()
        
        # Submit Information button
        if st.button("Submit Information"):
            insert_donor_with_donation(donor_data["dname"], donor_data["phno"], donor_data["daddress"], donor_data["donation_amount"], donor_data["donate_to"])

    if user_data["role"] == 'Volunteer':
        st.subheader("Volunteer Information")
        volunteer_data = {
            "vname": st.text_input("Enter Name:"),
            "phno": st.text_input("Enter Phone number:"),
            "availibility_start": st.date_input("Select Start date", datetime.date.today()),
            "availibility_end": st.date_input("Select End date", datetime.date.today()),
            "chosen_recipient": None
        }

        # Display the Recipient Table
        recipients_list = display_recipient_table()
        volunteer_data["chosen_recipient"] = st.text_input("Enter Recipient ID of whom you want to help:")

        # Submit Information button
        if st.button("Submit Information"):
            conn = get_database_connection()
            cursor = conn.cursor()
            try:
                insert_volunteer_query = "INSERT INTO Volunteer (name, phone_number, availability_start, availability_end) VALUES (%s, %s, %s, %s)"
                volunteer_values = (
                    volunteer_data["vname"],
                    volunteer_data["phno"],
                    volunteer_data["availibility_start"],
                    volunteer_data["availibility_end"]
                )
                cursor.execute(insert_volunteer_query, volunteer_values)
                volunteer_id = cursor.lastrowid  # Get the last inserted volunteer ID

                # Update the VolunteerRecipientMap table to associate the volunteer with the chosen recipient
                if volunteer_data["chosen_recipient"]:
                    insert_mapping_query = "INSERT INTO VolunteerRecipientMap (volunteer_id, recipient_id) VALUES (%s, %s)"
                    mapping_values = (volunteer_id, volunteer_data["chosen_recipient"][0])  # Use the recipient_id from the chosen_recipient tuple
                    cursor.execute(insert_mapping_query, mapping_values)

                conn.commit()
                st.success("Volunteer information submitted successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

    if user_data["role"] == 'Recipient':
        st.subheader("Recipient Information")
        recipient_data = {"rname": st.text_input("Recipient Name:"), "raddress": st.text_input("Recipient Address:"), "rcategory": st.selectbox("Recipient Category:", ['General', 'Educational', 'Healthcare', 'Disaster relief', 'Custom'])}

        # Submit Information button
        if st.button("Submit Information"):
            conn = get_database_connection()
            cursor = conn.cursor()
            try:
                insert_recipient_query = "INSERT INTO Recipient (name, address, category) VALUES (%s, %s, %s)"
                recipient_values = (recipient_data["rname"], recipient_data["raddress"], recipient_data["rcategory"])
                cursor.execute(insert_recipient_query, recipient_values)
                conn.commit()
                st.success("Recipient information submitted successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

# Section for reading data
if section == "Read":
    st.subheader("View Data")

    if user_data["role"] == 'Donor':
        st.subheader("Donor Information")
        display_donor_table()

    elif user_data["role"] == 'Volunteer':
        st.subheader("Volunteer Information")
        display_volunteer_table()

    elif user_data["role"] == 'Recipient':
        st.subheader("Recipient Information")
        display_recipient_table()

# Section for updating data
if section == "Update":
    st.subheader("Update Data")

    if user_data["role"] == 'Donor':
        st.subheader("Update Donor Information")
        donor_id = st.text_input("Enter Your Donor ID")
        donor_name = st.text_input("Enter New donor Name")
        phone_number = st.text_input("Enter new phone Number")
        address = st.text_input("Enter new Address")
        
        if st.button("Update Donor"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                update_donor_query = "CALL UpdateDonor(%s, %s, %s, %s)"
                donor_values = (donor_id, donor_name, phone_number, address)
                cursor.callproc('UpdateDonor', donor_values)
                conn.commit()
                st.success("Donor information updated successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

    elif user_data["role"] == 'Volunteer':
        st.subheader("Update Volunteer Information")
        volunteer_id = st.text_input("Enter Your Volunteer ID")
        volunteer_name = st.text_input("Enter Volunteer Name")
        phone_number = st.text_input("Enter Phone Number")
        start_date = st.date_input("Select Start Date", datetime.date.today())
        end_date = st.date_input("Select End Date", datetime.date.today())
        
        if st.button("Update Volunteer"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                update_volunteer_query = "CALL UpdateVolunteer(%s, %s, %s, %s, %s)"
                volunteer_values = (volunteer_id, volunteer_name, phone_number, start_date, end_date)
                cursor.callproc('UpdateVolunteer', volunteer_values)
                conn.commit()
                st.success("Volunteer information updated successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

    elif user_data["role"] == 'Recipient':
        st.subheader("Update Recipient Information")
        recipient_id = st.text_input("Enter Your Recipient ID")
        recipient_name = st.text_input("Enter Recipient Name")
        recipient_address = st.text_input("Enter Recipient Address")
        recipient_category = st.selectbox("Recipient Category:", ['General', 'Educational', 'Healthcare', 'Disaster relief', 'Custom'])

        if st.button("Update Recipient"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                update_recipient_query = "CALL UpdateRecipient(%s, %s, %s, %s)"
                recipient_values = (recipient_id, recipient_name, recipient_address, recipient_category)
                cursor.callproc('UpdateRecipient', recipient_values)
                conn.commit()
                st.success("Recipient information updated successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

# Section for deleting data
if section == "Delete":
    st.subheader("Delete Data")

    if user_data["role"] == 'Donor':
        st.subheader("Delete Donor Information")
        donor_id = st.text_input("Enter Donor ID to Delete")
        
        if st.button("Delete Donor"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                delete_donor_query = "CALL DeleteDonorAndRelatedData(%s)"
                donor_values = (donor_id,)
                cursor.callproc('DeleteDonorAndRelatedData', donor_values)
                conn.commit()
                st.success("Donor information deleted successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

    elif user_data["role"] == 'Volunteer':
        st.subheader("Delete Volunteer Information")
        volunteer_id = st.text_input("Enter Volunteer ID to Delete")
        
        if st.button("Delete Volunteer"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                delete_volunteer_query = "CALL DeleteVolunteerAndRelatedData(%s)"
                volunteer_values = (volunteer_id,)
                cursor.callproc('DeleteVolunteerAndRelatedData', volunteer_values)
                conn.commit()
                st.success("Volunteer information deleted successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

    elif user_data["role"] == 'Recipient':
        st.subheader("Delete Recipient Information")
        recipient_id = st.text_input("Enter Recipient ID to Delete")
        
        if st.button("Delete Recipient"):
            conn = get_database_connection()
            cursor = conn.cursor()
            
            try:
                delete_recipient_query = "CALL DeleteRecipientAndRelatedData(%s)"
                recipient_values = (recipient_id,)
                cursor.callproc('DeleteRecipientAndRelatedData', recipient_values)
                conn.commit()
                st.success("Recipient information deleted successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()
