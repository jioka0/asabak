# How to Install pgAdmin 4 (Web Mode) on Ubuntu Server

Since servers usually don't have a graphical interface, you'll need to install the **Web Version** of pgAdmin. This lets you access the database interface through your browser (e.g., `http://your-server-ip/pgadmin4`).

## Step 1: Add the pgAdmin Repository
Run these commands one by one on your server:

```bash
# 1. Install the public key for the repository
curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg

# 2. Create the repository configuration file
sudo sh -c 'echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
```

## Step 2: Install pgAdmin 4
Update your package lists and install the web version:

```bash
# 1. Update lists
sudo apt update

# 2. Install pgAdmin 4 Web Mode
sudo apt install pgadmin4-web
```

## Step 3: Configure pgAdmin
You need to set up an admin email and password to log in.

```bash
# Run the setup script
sudo /usr/pgadmin4/bin/setup-web.sh
```
*   **Email:** Enter your email address.
*   **Password:** Create a strong password.
*   **Generic Confirmation:** Say 'y' to creating the Apache/Web config.

## Step 4: Access pgAdmin
1.  Open your web browser.
2.  Go to: `http://YOUR_SERVER_IP/pgadmin4`
3.  Log in with the email and password you just created.
4.  Add your server connection (click "Add New Server").

---

## 💡 Alternative: The "Easy Way" (Command Line)
If you only need to run the migration script, you don't actually need to install pgAdmin on the server! You can use the built-in `psql` command which is likely already installed.

**To run your migration immediately without installing anything:**

1.  Upload the `migrate_likes_prod.sql` file to your server (e.g. using FileZilla or `scp`).
2.  Run this command:
    ```bash
    # Replace 'nekwasar_user' and 'nekwasar_db' with your actual info
    sudo -u postgres psql -d nekwasar_db -f migrate_likes_prod.sql
    ```
