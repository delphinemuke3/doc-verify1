FROM php:8.2-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    tesseract-ocr \
    libgl1 libglib2.0-0 \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY python/requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages -r /tmp/requirements.txt

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Copy project files
COPY . /var/www/html/

# Set permissions
RUN chown -R www-data:www-data /var/www/html/uploads \
    && chmod -R 777 /var/www/html/uploads

EXPOSE 80