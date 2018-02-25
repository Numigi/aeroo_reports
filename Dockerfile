FROM quay.io/numigi/odoo-base:11.0.5
MAINTAINER numigi <contact@numigi.com>

USER root

COPY ./report_aeroo /mnt/extra-addons/report_aeroo

EXPOSE 8069 8071
USER odoo
