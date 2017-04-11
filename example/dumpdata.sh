#!/bin/sh
[ -e "fixtures/example.json" ] && rm fixtures/example.json

./manage.py dumpdata \
    --indent=2 \
    --natural-foreign \
    email_auth \
    cms \
    cmsplugin_cascade \
    djangocms_text_ckeditor \
    filer \
    shop \
    shopit \
    --exclude shop.email \
    --exclude cmsplugin_cascade.segmentation \
    --exclude filer.clipboard \
    --exclude filer.clipboarditem \
    --exclude shopit.order \
    --exclude shopit.orderpayment \
    --exclude shopit.orderitem \
    --exclude shopit.cart \
    --exclude shopit.cartitem \
    --exclude shopit.cartdiscountcode \
    > fixtures/example.json
