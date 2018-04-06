FROM quay.io/numigi/odoo-public:11.0
MAINTAINER numigi <contact@numigi.com>

########
USER root
# Install dependencies for aeroo reports
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        openjdk-8-jre \
        pdftk \
    && rm -rf /var/lib/apt/lists/*

# we can't use `pip install --user` as the $HOME of odoo is a volume
# so everything that is installed in $HOME will be overwritten by the mounting.
COPY .docker_files/requirements.txt ./requirements.txt
RUN pip3 install -r ./requirements.txt && rm ./requirements.txt

USER odoo
########

COPY ./report_aeroo /mnt/extra-addons/report_aeroo

COPY .docker_files/main /mnt/extra-addons/main
COPY .docker_files/odoo.conf /etc/odoo
