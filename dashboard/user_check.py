from django.shortcuts import redirect
from Geoportal.settings import SESSION_NAME, ALLOWED_GROUPS
from Geoportal.utils import php_session_data
from useroperations.models import MbUser, MbGroup, MbUserMbGroup 
from django.contrib import messages
from django.utils.translation import gettext as _

def check_user(request):
    session_cookie = request.COOKIES.get(SESSION_NAME)
    if session_cookie is not None:
        session_data_mapbender = php_session_data.get_mapbender_session_by_memcache(session_cookie)
        if session_data_mapbender is not None:
            if b'mb_user_id' in session_data_mapbender:
                userid = session_data_mapbender[b'mb_user_id']
                try:
                    user = MbUser.objects.get(mb_user_id=userid)
                except MbUser.DoesNotExist:
                    messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
                    return redirect('useroperations:index')

                # Check if the user belongs to the allowed group(s)
                allowed_groups = ALLOWED_GROUPS
                user_groups = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_name', flat=True)
                if not any(group in allowed_groups for group in user_groups):
                    messages.add_message(request, messages.ERROR, _("You do not have the necessary permissions to access this page."))
                    return redirect('useroperations:index')
                return user
            else:
                messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
                return redirect('useroperations:index')
            
            # if user is None:
            #     messages.add_message(request, messages.ERROR, _("You do not have the necessary permissions to access this page.!"))
            #     return redirect('useroperations:index')
        else:
            messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
            return redirect('useroperations:index')
    else:
        messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
        return redirect('useroperations:index')
    
def check_user_login(request):
    session_cookie = request.COOKIES.get(SESSION_NAME)
    if session_cookie is not None:
        session_data_mapbender = php_session_data.get_mapbender_session_by_memcache(session_cookie)
        if session_data_mapbender is not None:
            if b'mb_user_id' in session_data_mapbender:
                userid = session_data_mapbender[b'mb_user_id']
                try:
                    user = MbUser.objects.get(mb_user_id=userid)
                except MbUser.DoesNotExist:
                    return redirect('useroperations:index')

                # Check if the user belongs to the allowed group(s)
                allowed_groups = ALLOWED_GROUPS
                user_groups = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_name', flat=True)
                if not any(group in allowed_groups for group in user_groups):
                    return redirect('useroperations:index')
                return user
            else:
                return redirect('useroperations:index')
            
            # if user is None:
            #     messages.add_message(request, messages.ERROR, _("You do not have the necessary permissions to access this page.!"))
            #     return redirect('useroperations:index')
        else:
            return redirect('useroperations:index')
    else:
        return redirect('useroperations:index')