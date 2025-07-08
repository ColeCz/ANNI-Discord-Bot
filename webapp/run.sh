#!/bin/bash
set -e

# Load env vars (avoids exporting globally)
set -o allexport
source form_site/.env
set +o allexport

echo "Running DB init scripts..."

# First: Create the user (only)
template=../database/db-init-scripts/10-create-user.sql.template
script="${template%.sql.template}.sql"
echo "Creating temp SQL file: $script"
envsubst < "$template" > "$script"
sudo -u postgres psql -f "$script"
rm "$script"

# Then: Create the database if it doesn't exist
echo "Checking if DB exists..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    echo "Creating database ${DB_NAME}..."
    sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"
else
    echo "Database ${DB_NAME} already exists. Skipping creation."
fi

# Finally: Run the rest of the scripts (skipping 10-*)
for template in ../database/db-init-scripts/*.template; do
    if [[ "$template" == *10-create-user.template ]]; then
        continue  # already handled
    fi
    script="${template%.template}.sql"
    echo "Creating temp SQL file: $script"
    envsubst < "$template" > "$script"
    sudo -u postgres psql -f "$script"
    rm "$script"
done

echo "Database initialization successful."

echo "Connecting Backend..."
python3 manage.py makemigrations
python3 manage.py migrate

echo "Success: setup complete."

python3 manage.py runserver
