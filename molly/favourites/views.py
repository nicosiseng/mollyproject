from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import resolve

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import lazy_reverse, Breadcrumb, BreadcrumbFactory

from molly.favourites import get_favourites
from molly.favourites.models import Favourite

class FavouritableView(BaseView):
    """
    A view to inherit from if you want to be favouritable
    """
    
    def initial_context(self, request, *args, **kwargs):
        
        context = super(FavouritableView, self).initial_context(request, *args, **kwargs)
        
        # Add whether or not this is favouritable to the context
        context['is_favouritable'] = True
        
        # Also, add whether or not this particular thing already is favourited
        context['is_favourite'] = Favourite.objects.filter(user= request.user,
                                                           url = request.path_info).exists()
        
        # And the URL of this page (so it can be favourited)
        context['favourite_url'] = request.path_info
        
        return context

class IndexView(BaseView):
    """
    Allows for favourites management
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Favourites',
            lazy_reverse('index'),
        )
    
    def handle_GET(self, request, context):
        """
        Show a list of favourited things, and allow removal of these
        """
        context['favourites'] = get_favourites(request)
        return self.render(request, context, 'favourites/index')
    
    def handle_POST(self, request, context):
        """
        Add and remove favourites. Favourites are stored as URLs (the part of
        them Django is interested in anyway) in the database. This has the
        downside of breaking favourites if URLs change.
        """
        
        # Alter favourites list
        if 'URL' in request.POST:
            
            if 'favourite' in request.POST:
                # Add
                try:
                    resolve(request.POST['URL'])
                except Http404:
                    # This means that they tried to save a URL that doesn't exist
                    # or isn't on our site
                    return HttpResponseRedirect(lazy_reverse('favourites:index'))
                else:
                    Favourite(user=request.user, url=request.POST['URL']).save()
            
            elif 'unfavourite' in request.POST:
                Favourite.objects.filter(user=request.user, url=request.POST['URL']).delete()
        
            # If the source was the favourites page, redirect back there
            if 'return_to_favourites' in request.POST:
                return self.handle_GET(request, context)
            
            # else the source
            else:
                return HttpResponseRedirect(request.POST['URL'])
            
        else:
            # Missing POST data, probably a bad request
            return HttpResponseRedirect(lazy_reverse('favourites:index'))