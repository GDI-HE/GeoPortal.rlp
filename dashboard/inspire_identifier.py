
from useroperations.models import  Wms, MbGroup, MbUserMbGroup , Layer, LayerKeyword
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from dashboard.user_check import check_user
from dashboard.models import InspireCategory, InspireCategories_detail, IsoCategory, IsoTopicCategory



def inspire_identifier(request):
    #get all the keywords present in the layers
    
    #first task: get all the layers
            search_query = request.GET.get('search', '')
            user = check_user(request)
            if isinstance(user, HttpResponseRedirect):
                return user  # Redirect if the user is not authenticated or does not have permissions

            userid = user.mb_user_id
            user_group_ids = MbGroup.objects.filter(
                mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
            ).values_list('mb_group_id', flat=True)

            # Filter WMS services based on the search query
            if search_query:
                wms_services = Wms.objects.filter(
                    Q(wms_id__icontains=search_query) | Q(wms_title__icontains=search_query),
                    fkey_mb_group_id = user_group_ids
                ).order_by('wms_id')
            else:
                user_group_ids = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_id', flat=True)
                wms_services = Wms.objects.filter(fkey_mb_group_id__in=user_group_ids).order_by('wms_id')

            # Aggregate data across all pages
            all_layers = Layer.objects.filter(fkey_wms_id__in=wms_services).distinct()


            # Paginate the WMS services
            paginator = Paginator(wms_services, 1000)  # Show 10 WMS services per page
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)

            data_inspire = []

         

            for wms in page_obj:
                # Get all unique layers for this WMS
                layers = Layer.objects.filter(fkey_wms_id=wms).distinct()

                # Fetch all keywords for these layers
                keywords_present = list(
                    LayerKeyword.objects.filter(fkey_layer__in=layers)
                    .values_list('fkey_keyword__keyword', flat=True)
                )

                # Check if 'inspireidentifiziert' is present in keywords
                if 'inspireidentifiziert' in keywords_present:
                    inspire_categories = InspireCategory.objects.filter(fkey_layer_id__in=layers)
                    #just to check the category_code. Remove later
                    if inspire_categories.exists():
                        # Loop through all matching InspireCategory objects
                        for inspire_category in inspire_categories:
                            # Get the foreign key value (an integer)
                            fkey_inspire_category_id = inspire_category.fkey_inspire_category_id

                            # Query the InspireCategories_detail table for a matching entry
                            matching_category = InspireCategories_detail.objects.filter(inspire_category_id=fkey_inspire_category_id).first()
                            if matching_category:
                                inspire_category_code = matching_category.inspire_category_code_en

                        data_inspire.append({
                            'wms': wms,
                            'status': 'Inspire category exists',  
                            'color': 'green',
                            'inspire_category_code': inspire_category_code
                        })
                    else:
                        data_inspire.append({
                            'wms': wms,
                            'status': 'Keyword as Inspireidentifiziert but Inspire category missing', 
                            'color': 'red',
                            'inspire_category_code': 'None'
                        })
                else:
                    inspire_categories = InspireCategory.objects.filter(fkey_layer_id__in=layers)
                    if inspire_categories.exists():
                        # Loop through all matching InspireCategory objects
                        for inspire_category in inspire_categories:
                            # Get the foreign key value (an integer)
                            fkey_inspire_category_id = inspire_category.fkey_inspire_category_id

                            # Query the InspireCategories_detail table for a matching entry
                            matching_category = InspireCategories_detail.objects.filter(inspire_category_id=fkey_inspire_category_id).first()
                            if matching_category:
                                inspire_category_code = matching_category.inspire_category_code_en

                    if inspire_categories.exists():
                        data_inspire.append({
                            'wms': wms,
                            'status': 'Inspire Category but keyword missing',  
                            'color': 'mildred',
                            'inspire_category_code': inspire_category_code 
                        })
                    else:
                        data_inspire.append({
                            'wms': wms,
                            'status': 'No Inspire Category, nor inspireidentifiziert',  
                            'color': 'white',
                            'inspire_category_code': 'None'
                        })
                
            return data_inspire


                

    #check if the layer has keyword inspire_identifiziert

    #if yes check the table layer_inspire_categorey and check if fkey_layer_id and fkey_inspire_category_id are associated

    #check if inspire_category table has anything to do if nothing works

from itertools import chain
def iso_categorised(request):
            search_query = request.GET.get('search', '')
            user = check_user(request)
            if isinstance(user, HttpResponseRedirect):
                return user  # Redirect if the user is not authenticated or does not have permissions

            userid = user.mb_user_id
            user_group_ids = MbGroup.objects.filter(
                mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
            ).values_list('mb_group_id', flat=True)

            # Filter WMS services based on the search query
            if search_query:
                wms_services = Wms.objects.filter(
                    Q(wms_id__icontains=search_query) | Q(wms_title__icontains=search_query),
                    fkey_mb_group_id = user_group_ids
                ).order_by('wms_id')
            else:
                user_group_ids = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_id', flat=True)
                wms_services = Wms.objects.filter(fkey_mb_group_id__in=user_group_ids).order_by('wms_id')

            # Aggregate data across all pages
            all_layers = Layer.objects.filter(fkey_wms_id__in=wms_services).distinct()


            # Paginate the WMS services
            paginator = Paginator(wms_services, 1000)  # Show 10 WMS services per page
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)

            data_iso = []

         

            for wms in page_obj:
                # Get all unique layers for this WMS
                layers = Layer.objects.filter(fkey_wms_id=wms).distinct()
                iso_categories = IsoCategory.objects.filter(fkey_layer_id__in=layers)
                if iso_categories.exists():
                        #print(f"  Iso Category: {iso_category.fkey_md_topic_category_id}")
                        for iso_cat in iso_categories:
                            iso_category = iso_cat.fkey_md_topic_category
                        iso_name = IsoTopicCategory.objects.filter(md_topic_category_id=iso_category).values_list('md_topic_category_code_de', flat=True)
                        for keywords in iso_name:
                             category = keywords
                            
                        data_iso.append({
                            'wms_iso': wms,
                            'status_iso': 'ISO category exists',  
                            'color_iso': 'green-iso',
                            'category': category
                        
                        })
                else:
                        data_iso.append({
                            'wms_iso': wms,
                            'status_iso': 'ISO category doesnot exists',  
                            'color_iso': 'white-iso',
                            'category': 'None'
                        })
                         
            return data_iso
