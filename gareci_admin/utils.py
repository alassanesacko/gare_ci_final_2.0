from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'
    def test_func(self):
        return self.request.user.is_staff


class ActiveTabMixin: #activé si on est dans la page 
    active_tab_value = None 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.active_tab_value:
            context['active_tab'] = self.active_tab_value
        return context
    
class BreadcrumbMixin:
    breadcrumb_title = None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.breadcrumb_title:
            context['breadcrumb_title'] = self.breadcrumb_title
        return context