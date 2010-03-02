from xml.sax.saxutils import escape
from datetime import date
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.renderers import mobile_render

from ..models import Feed, Item

class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'Events',
            'additional': 'Upcoming events from across the University and city',
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'events', None, 'Events', lazy_reverse('events_index')
        )
        
    def handle_GET(cls, request, context):
        feeds = Feed.events.all()
        context['feeds'] = feeds
        return mobile_render(request, context, 'rss/index')

class ItemListView(BaseView):
    def get_metadata(cls, request, slug):
        feed = get_object_or_404(Feed.events, slug=slug)
        
        return {
            'last_modified': feed.last_modified,
            'title': feed.title,
            'additional': '<strong>Events feed</strong> %s' % feed.last_modified.strftime('%a, %d %b %Y'),
        }
    
    def initial_context(cls, request, slug):
        feed = get_object_or_404(Feed.events, slug=slug)
        return {
            'feed': feed,
            'items': feed.item_set.filter(dt_start__gte=date.today()).order_by('dt_start'),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug):
        return Breadcrumb(
            'events',
            lazy_parent(IndexView),
            context['feed'].title,
            lazy_reverse('events_item_list', args=[slug])
        )
        
    def handle_GET(cls, request, context, slug):
        return mobile_render(request, context, 'rss/event_list')

class ItemDetailView(BaseView):
    def get_metadata(cls, request, slug, id):
        item = get_object_or_404(Item.events, feed__slug=slug, id=id)
        
        return {
            'last_modified': item.last_modified,
            'title': item.title,
            'additional': '<strong>News item</strong>, %s, %s' % (escape(item.feed.title), item.last_modified.strftime('%a, %d %b %Y')),
        }

    def initial_context(cls, request, slug, id):
        item = get_object_or_404(Item.events, feed__slug=slug, id=id)
        return {
            'item': item,
            'feed': item.feed,
            'zoom': cls.get_zoom(request),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug, id):
        return Breadcrumb(
            'events',
            lazy_parent(ItemListView, slug=slug),
            context['item'].title,
            lazy_reverse('events_item_detail', args=[slug,id])
        )
        
    def handle_GET(cls, request, context, slug, id):
        context.update({
            'description': context['item'].get_description_display(request.device)
        })
        return mobile_render(request, context, 'rss/event_detail')
