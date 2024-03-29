FROM quay.io/numigi/odoo-public:14.latest
MAINTAINER numigi <contact@numigi.com>

########
USER root
# Install dependencies for aeroo reports
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre \
        libreoffice-java-common \
        libreoffice-writer \
        poppler-utils

# we can't use `pip install --user` as the $HOME of odoo is a volume
# so everything that is installed in $HOME will be overwritten by the mounting.
COPY .docker_files/requirements.txt ./requirements.txt
RUN pip3 install -r ./requirements.txt && rm ./requirements.txt

USER odoo
########

COPY ./account_check_printing_aeroo /mnt/extra-addons/account_check_printing_aeroo
COPY ./report_aeroo /mnt/extra-addons/report_aeroo
COPY ./report_aeroo_invoice /mnt/extra-addons/report_aeroo_invoice
COPY ./report_aeroo_replace_qweb /mnt/extra-addons/report_aeroo_replace_qweb

COPY .docker_files/main /mnt/extra-addons/main
COPY .docker_files/odoo.conf /etc/odoo
