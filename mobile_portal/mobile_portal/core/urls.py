from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('mobile_portal.core.views',

    (r'^$', 'index', {}, 'core_index'),
    (r'^core/ajax/update_location/$', 'ajax_update_location', {}, 'core_ajax_update_location'),
    (r'^core/update_location/$', 'update_location', {}, 'core_update_location'),

    (r'^customise/$', 'customise', {}, 'core_customise'),
)