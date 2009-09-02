# Create your views here.
import urllib
from xml.etree import ElementTree as ET
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from mobile_portal.podcasts.models import Podcast, PodcastCategory
from mobile_portal.podcasts import TOP_DOWNLOADS_RSS_URL
from mobile_portal.wurfl import device_parents

OPML_FEED = 'http://rss.oucs.ox.ac.uk/oxitems/podcastingnewsfeeds.opml'

def index(request):
    show_itunesu_link = not request.device.devid in request.preferences['podcasts']['use_itunesu']
    if 'show_itunesu_link' in request.GET:
        show_itunesu_link = request.GET['show_itunesu_link'] != 'false'

    #if "apple_iphone_ver1" in device_parents[request.device.devid] :
    #        return HttpResponseRedirect ("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
    context = {
        'categories': PodcastCategory.objects.all(),
        'show_itunesu_link': show_itunesu_link
    }    
    
    return mobile_render(request, context, 'podcasts/index')

def category_detail(request, code, medium=None):
    category = get_object_or_404(PodcastCategory, code=code)
    podcasts = Podcast.objects.filter(category=category)
    if medium:
        podcasts = podcasts.filter(medium=medium)

    context = {
        'category': category,
        'podcasts': podcasts,
        'medium': medium,
    }
    return mobile_render(request, context, 'podcasts/category_detail')

def podcast_detail(request, code=None, id=None, podcast=None):
    if not podcast:
        podcast = get_object_or_404(Podcast, category__code=code, id=id)
    
    items = podcast.podcastitem_set.order_by('order','-published_date')
    
    context = {
        'podcast': podcast,
        'items': items,
    }
    
    return mobile_render(request, context, 'podcasts/podcast_detail')

def top_downloads(request):
    return podcast_detail(
        request,
        podcast=Podcast.objects.get(rss_url=TOP_DOWNLOADS_RSS_URL)
    )

def itunesu_redirect(request):
    use_itunesu = request.POST.get('use_itunesu') == 'yes'
    remember = 'remember' in request.POST
    
    if remember:
        request.preferences['podcasts']['use_itunesu'][request.device.devid] = use_itunesu
    
    if request.method == 'POST' and 'no_redirect' in request.POST:
        return HttpResponse('', mimetype="text/plain")
    elif request.method == 'POST' and not use_itunesu:
        if remember:
            return HttpResponseRedirect(reverse('podcasts_index'))
        else:
            return HttpResponseRedirect(reverse('podcasts_index') + '?show_itunesu_link=false')
    else:
        return HttpResponseRedirect("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
        