set -o errexit


pip install -r requirements.txt

cd ytdownloader
python manage.py collectstatic --no-input
python manage.py migrate