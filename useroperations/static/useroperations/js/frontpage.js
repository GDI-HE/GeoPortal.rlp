/**
 * Returns the cookie if found
 */
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function resizeIframe(obj) {
  obj.style.height = obj.contentWindow.document.body.scrollHeight + 'px';
}

function setCookie(cname, cvalue){
    document.cookie = cname + "=" + cvalue + ";path=/;SameSite=Lax";
}

function startSearch(){
    // since the all.js might be loaded slower or faster, we need to make sure it exists before we call prepareAndSearch()
    // which lives in all.js
    var script = $("#all-script");
    $(script).ready(function(){
        // Collect query parameters
        var inputTerms = $(".-js-simple-search-field").val().trim();
        search.setParam("terms", inputTerms);

        // collapse extended search if open
        var extendedSearchHeader = $(".-js-extended-search-header");
        if(extendedSearchHeader.hasClass("active")){
            extendedSearchHeader.click();
        }
        prepareAndSearch(); // search and render
    });

}

/**
 * Resize the sidebar's height according to the body content height.
 * If the body does not provide enough content to wrap the sidebar, the body needs to be resized!
 */
function resizeSidebar(){
    var sidebar = $(".sidebar-wrapper");
    var content = $(".body-content .wrapper");
    var body = $("#body-content");

    var contentLength = content.outerHeight();
    var sidebarLength = sidebar.outerHeight();

    if(sidebar.outerHeight() != body.outerHeight()){
        sidebar.outerHeight(body.outerHeight());
    }
}

function resizeMapOverlay(){
    var elem = $(this);
    var mapLayer = $(".map-viewer-overlay");
    var bodyContent = $(".body-content");
    mapLayer.outerHeight(bodyContent.outerHeight());
}

/*
 * Switch between mobile and default map viewer
 */
function toggleMapViewers(target){
    var iframe = $("#mapviewer");
    var oldSrc = iframe.attr("data-toggle");
    var src = iframe.attr("src");
    if(src !== oldSrc){
        iframe.attr("data-toggle", src);
        iframe.attr("src", oldSrc);
        iframe.toggleClass("mobile-viewer");
    }
}

function toggleSubMenu(elem){
    var elem = $(elem);
    elem.parents().children(".sidebar-area-content").slideToggle("slow");
}

function toggleMapviewer(servicetype){
    // for dsgvo not accepted
    if ($("#dsgvo").val() == "False"){
    window.location.href = "/change-profile";
    return;
    }
    //mobile
    if ($(window).width() < 689 || /Mobi|Tablet|android|iPad|iPhone/.test(navigator.userAgent)) {
        // servicetype is true when coming from search
        if (servicetype) {
            // start mobile from wms search
            if (servicetype.match(/wms/)){
                var layerid=servicetype.match(/\d+/);
                window.location.href = window.location.href.split('/').slice(0, 3).join('/')+'/mapbender/extensions/mobilemap2/index.html?layerid='+layerid[0];
            // start mobile from wmc search
            } else if (servicetype.match(/wmc/)) {
                var wmcid=servicetype.match(/\d+/);
                window.location.href = window.location.href.split('/').slice(0, 3).join('/')+'/mapbender/extensions/mobilemap2/index.html?wmc_id='+wmcid[0];
            // start mobile with default mobile wmc (from index)
            }
        }else{
            window.location.href = window.location.href.split('/').slice(0, 3).join('/')+'/mapbender/extensions/mobilemap2/index.html?';
        }
    }else{
        // get preferred gui
        var toggler = $(".map-viewer-toggler");
        var preferred_gui = toggler.attr("data-gui");

        // start loading the iframe content
        var iframe = $("#mapviewer");
        var src = iframe.attr("src");
        var dataParams = iframe.attr("data-resource");

        // change mb_user_gui Parameter if default gui  differs
        var url = new URL(dataParams)
        var params = new URLSearchParams(url.search);
        if(preferred_gui == "Geoportal-Hessen-2019" || preferred_gui.length == 0 ){
            params.set('gui_id',"Geoportal-Hessen-2019")
        }else{
            params.set('gui_id', preferred_gui)
        }
        url.search = params.toString();
        dataParams = url.toString();
        var dataToggler = iframe.attr("data-toggle");

        if(dataParams !== src && (dataToggler == src || src == "about:blank")){
            iframe.attr("src", dataParams);
        }
        // resize the overlay
        var mapLayer = $(".map-viewer-overlay");
        resizeMapOverlay();
        // let the overlay slide in
        mapLayer.slideToggle("slow")
        mapLayer.toggleClass("closed");
        // close the sidebar
        if(!$(".sidebar-wrapper").hasClass("closed")){
            $(".sidebar-toggler").click();
        }
	$('body').toggleClass("mapviewer-opened");
        $('#sidebar').toggleClass("mapviewer-opened-force-scroll");
        window.scrollTo({top:0,left:0,behavior:'smooth'});
        // change mapviewer-button to back-button
        $('.map-viewer-toggler').toggleClass('backbutton');
        $('.map-viewer-toggler').toggleClass('nobackbutton');
    }
}

/**
 * Reset the search catalogue source back to 'primary'.
 * If a user selects e.g. the european search catalogue, goes back to the landing page
 * and reopens the search module again, the european catalogue will still be selected. This is not the
 * behaviour we want.
 */
function resetSearchCatalogue(src){
    // reset catalogue source to primary if we are not in the search module
    if(!location.pathname.includes("search") && search.getParam("source") != src){
        search.setParam("source", src)
    }
}

/**
 * If the search page is reloaded, e.g. due to language changing or normal F5 reload,
 * we need to make sure the search starts again automatically. Otherwise the users will be confused and cry.
 */
function startAutomaticSearch(){
    // wait until the document is loaded completely, then start the automatic search!
    $(document).ready(function(){
        if(location.pathname.includes("search")){
            var searchBody = $(".search-overlay-content");
            if(searchBody.html().trim().length == 0){
                prepareAndSearch();
            }
        }

    });
}

function fallbackCopyTextToClipboard(text) {
  var textArea = document.createElement("textarea");
  textArea.value = text;

  // Avoid scrolling to bottom
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.position = "fixed";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    var successful = document.execCommand('copy');
    var msg = successful ? 'successful' : 'unsuccessful';
    console.log('Fallback: Copying text command was ' + msg);
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
  }

  document.body.removeChild(textArea);
}
function copyTextToClipboard(text) {
  if (!navigator.clipboard) {
    fallbackCopyTextToClipboard(text);
    return;
  }
  navigator.clipboard.writeText(text).then(function() {
    console.log('Async: Copying to clipboard was successful!');
  }, function(err) {
    console.error('Async: Could not copy text: ', err);
  });
}

$(document).on("click", ".share-button", function(){

    //landing page
    if ($(".landing-page-headline")[0]){
      var elem = $(this).parents(".tile").find(".tile-header");
    //search
    } else {
      var elem = $(this).parents(".resource-element-actions").find(".share-button")
    }

    var id = elem.attr("data-id");
    type = id.split("=")[0];
    id = id.split("=")[1];

    copyTextToClipboard(window.location.origin+"/map?"+type+"="+id);
    var popup = document.getElementsByName("sharepopup"+id);

    for (var i = 0; i < popup.length; i++) {
      popup[i].classList.add("show-popup");

      setTimeout(function(){
        $(".popuptext-landing."+id).removeClass( "show-popup" );
        $(".popuptext-search."+id).removeClass( "show-popup" )  }, 3000);

    }

});


$(document).on("click", ".mobile-button", function(){
    // get wmc id
    var elem = $(this).parents(".tile").find(".tile-header");
    var id = elem.attr("data-id");
    // get rid of 'WMC=' which is needed for the usual call
    id = id.split("=")[1];
    openInNewTab("/mapbender/extensions/mobilemap2/index.html?wmc_id=" + id);
});

$(document).on("click", ".map-viewer-selector", function(){
    var elem = $(this);
    var mapViewerSelector = $(".map-applications-toggler");

    elem.toggleClass("open")
    // close other menu
    if(mapViewerSelector.hasClass("open") && elem.hasClass("open")){
        mapViewerSelector.click();
    }

    var viewerList = $(".map-viewer-list");
    viewerList.slideToggle("medium");

    var sideBar = elem.closest(".map-sidebar");
    if((mapViewerSelector.hasClass("open") || elem.hasClass("open")) && !sideBar.hasClass("open")){
        sideBar.addClass("open");
    }else if(!mapViewerSelector.hasClass("open") && !elem.hasClass("open") && sideBar.hasClass("open")){
        sideBar.removeClass("open");
    }
});

$(document).on("click", ".map-applications-toggler", function(){
    var elem = $(this);
    var mapViewerSelector = $(".map-viewer-selector");

    elem.toggleClass("open")
    // close other menu
    if(mapViewerSelector.hasClass("open") && elem.hasClass("open")){
        mapViewerSelector.click();
    }

    var applicationsList = $(".map-applications-list");
    applicationsList.slideToggle("medium");

    var sideBar = elem.closest(".map-sidebar");
    if((mapViewerSelector.hasClass("open") || elem.hasClass("open")) && !sideBar.hasClass("open")){
        sideBar.addClass("open");
    }else if(!mapViewerSelector.hasClass("open") && !elem.hasClass("open") && sideBar.hasClass("open")){
        sideBar.removeClass("open");
    }
});

$(document).on("click", ".map-viewer-list-entry", function(){
    var elem = $(this);
    var iFrame = $("#mapviewer");

    // move viewport for user

    gui_id = elem.attr("data-resource");
    if(gui_id.includes("http")){
        // simply paste in the new url
        iFrame.attr("src", gui_id);
    }else{
        var srcUrl = null;
        if(!iFrame.attr("src").includes("gui_id")){
            // there is a url in the src which can not be changed directly. We need to go back to the fallback uri!
            srcUrl = iFrame.attr("data-resource");
        }else{
            // this is just another gui id, we need to put it inside the matching parameter
            srcUrl = iFrame.attr("src");
        }
        var url = new URL(srcUrl);
        var searchParams = new URLSearchParams(url.search);
        searchParams.set("gui_id", gui_id);

        url.search = searchParams.toString();
        src = url.toString();

        iFrame.attr("src", src);
    }

    // close menu
    //$(".map-viewer-selector").click();
});

$(document).on("click", ".map-applications-list-entry", function(){
    var elem = $(this);
    var iframe = $("#mapviewer");

    // move viewport for user
    window.scrollTo({
        top:0,
        left:0,
        behavior:'smooth'
    });

    iframeSrc = iframe.attr("src").toString();
    iframeDataParams = iframe.attr("data-resource").toString();

    var srcUrl = new URL(iframeDataParams);
    var params = new URLSearchParams(srcUrl.search);
    params.set('gui_id',elem.attr("data-id"))

    srcUrl.search = params.toString();
    src = srcUrl.toString();

    iframe.attr("src", src);

    // close list menu
    //$(".map-applications-toggler").click();

});

$(document).on("keypress", "#id_message", function(){
    var elem = $(this);
    var out = $(".foot-note span");
    var maxLength = elem.attr("maxlength");
    var restLength = maxLength - elem.val().length;
    if((restLength == 0 && !out.hasClass("warning")) ||
        (restLength > 0 && out.hasClass("warning"))){
        out.toggleClass("warning");
    }
    out.html(restLength);
});

/*
 * Handles the sidebar toggler functionality
 */
$(document).on("click", ".sidebar-toggler", function(){
    var elem = $(this);
    var sidebar = $(".sidebar-wrapper");
    var bodyContent = $("#body-content");
    sidebar.toggleClass("closed");
    var isClosed = sidebar.hasClass("closed");
    setCookie("sdbr-clsd", isClosed);
    bodyContent.toggleClass("sidebar-open");
});

/*
 * Handles the sidebar toggler functionality
 */
$(document).on("click", ".map-viewer-button", function(){
    var elem = $(this);
    var form = $("#map-viewer-selector");
    form.toggle("fast");
});

$(".body-content").change(function(){
});

$(document).on("click", "#geoportal-search-button", function(){
    // for dsgvo not accepted
    if ($("#dsgvo").val() == "False"){
        window.location.href = "/change-profile";
        return;
    }

    // check if the search page is already opened
    if(!window.location.pathname.includes("/search")){
        // no index page loaded for search -> load it!
        // we lose all searchbar data on reloading, so we need to save it until the page is reloaded
        //window.sessionStorage.setItem("startSearch", true);
        window.sessionStorage.setItem("searchbarBackup", $(".-js-simple-search-field").val().trim());
        window.sessionStorage.setItem("isSpatialCheckboxChecked", $("#spatial-checkbox").is(":checked"));
        window.location.href = "/search";
    }else{
        startSearch();
        if (!$(".map-viewer-overlay").hasClass("closed")){
            toggleMapviewer();
        }
    }

});


 $(document).on("click", ".quickstart.search", function(event){
     event.preventDefault();
     var elem = $(this);
     var resource = elem.attr("data-resource");
     var searchButton = $("#geoportal-search-button");
     search.setParam("singleResourceRequest", resource);
     search.setParam("source", "primary");
     searchButton.click();
 });

 $(document).on("click", ".topics .tile-header", function(){
     var elem = $(this);
     var filterName = elem.attr("data-name");
     var filterId = elem.attr("data-id");
     var searchButton = $("#geoportal-search-button");
     const searchCategory = elem.attr("data-search-category");
     search.setParam("facet", [searchCategory, filterName, filterId].join(","));
     searchButton.click();
 });

 $(document).on("hover", ".topics .tile-header", function(){
     var elem = $(this).children(".tile-header-img").children(".tile-img");
     elem.toggleClass("highlight");
 });


 $(document).on("click", ".favourite-wmcs .tile-header", function(event){
    event.preventDefault();
    var elem = $(this);
    if(elem.attr("id") == "show-all-tile-content"){
        $("#geoportal-search-button").click();
        return;
    }
    href = elem.attr("data-id");
    //if($("#mapviewer").hasClass("mobile-viewer")){
    //    toggleMapViewers();
    //}
    startAjaxMapviewerCall(href);

 });

$(document).on("click", ".message-toggler", function(){
    var elem = $(this);
    elem.toggle();
    elem.parent().toggle();
});


// Password message popup
$(document).on('focus blur', "#id_password", function(){
    // use nice transition css hack from
    // https://css-tricks.com/content-jumping-avoid/
    $("#password_message").toggleClass("in");
    setTimeout(resizeSidebar, 1000);
});

$(document).on('click', ".sidebar-area", function(){

if ($(window).width() < 689) {
    var elem = this.innerHTML;
    // check if there is a submenu at the sidebar area
    if (elem.indexOf("toggleSubMenu") < 0){
        if(!$(".sidebar-wrapper").hasClass("closed")){
                $(".sidebar-toggler").click();
        }

    }
}
});


$(document).on('click', ".sidebar-list-element", function(){
if ($(window).width() < 689) {
         if(!$(".sidebar-wrapper").hasClass("closed")){
            $(".sidebar-toggler").click();
         }
}

});



// $(document).on('click', "#change-form-button", function(event){

//   var userLang = navigator.language || navigator.userLanguage;
//   var PasswordInput = document.getElementById("password");
//   var PasswordInputConfirm = document.getElementById("id_passwordconfirm");


//   if(PasswordInput.value != PasswordInputConfirm.value) {
//     if(userLang == "de") {
//       alert("Passwörter stimmen nicht überein");
//     } else {
//       alert("Passwords do not match");
//     }
//     event.preventDefault();

//   }


// });

//captcha refresh
$(function() {
    if (typeof refreshCaptcha !== 'undefined') {
    $('img.captcha').after(
        $('<a href="#void" class="captcha-refresh" aria-label="' + refreshCaptcha + '" title="' + refreshCaptcha + '">↻</a>')
         );
    $('.captcha-refresh').click(function(){
        var $form = $(this).parents('form');
        var url = location.protocol + "//" + window.location.hostname + ":"
                  + location.port + "/captcha/refresh/";

        // Make the AJAX-call
        $.getJSON(url, {}, function(json) {
            $form.find('input[name="captcha_0"]').val(json.key);
            $form.find('img.captcha').attr('src', json.image_url);
        });

        return false;
    });
    }
  });

/* BEGIN resizeObserver bodyContent */
$(document).ready(function(){
    bodyBoxElement = document.querySelector('#body-content');

    let resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
            // do sth here
	    resizeSidebar();
        }
    });

    resizeObserver.observe(bodyBoxElement);

});
/* END resizeObserver bodyContent */

/*
 * Contains functions that shall be executed when the page is reloaded
 */
$(window).on("load", function(param){
    var searchbar = $(".-js-simple-search-field");
    var checkbox = $("#spatial-checkbox");
    if (window.sessionStorage.getItem("isSpatialCheckboxChecked") == 'true'){
        checkbox.prop("checked", true);
    }

    var searchbarBackup = window.sessionStorage.getItem("searchbarBackup");
    if (searchbarBackup !== null){
        searchbar.val(searchbarBackup);
        window.sessionStorage.removeItem("searchbarBackup");
    }
    window.sessionStorage.removeItem("isSpatialCheckboxChecked");

    var current_page_area = $(".current-page").parents(".sidebar-area-content");
    current_page_area.show();

    // check if a service is called via GET (wmc or wms)
    var route = location.pathname;
    var params = location.search;
    if(route.includes("/map")){
        var params = location.search;
        if(params.length > 0 ){
            params = params.replace("?", "");
            startAjaxMapviewerCall(params);
        }
    }

});

var lastClickedTab = 'rank';
var activeTab = 'mostusedWMC';

$(document).ready(function() {
    if (window.location.pathname === '/') {
        $('#mostusedWMC').click(function(event) {
            event.preventDefault();
            lastClickedTab = 'rank';
            activeTab = 'mostusedWMC';
            currentPage=1;
            currentSet=1;
            loadPage(1, false, lastClickedTab);
        });

        $('#newWMC').click(function(event) {
            event.preventDefault();
            lastClickedTab = 'date';
            activeTab = 'newWMC';
            currentPage=1;
            currentSet=1;
            loadPage(1, false, lastClickedTab);
        });

        loadPage(1, false, lastClickedTab);
    }
});


//The pagination part is hard-coded and only works when the max_results=5 (set in settings.py as MAX_RESULTS = 5). 
//If max_results=10 to be used; for example, the js codes need to be changed accordingly.
var currentPage = 1;
var totalPages;
var currentSet = 1;
var GoToPage, Back, Next, GoToPrevious, GoToNext, ShowAllWMCs; //define variable so that it won't create console error when the variable is not defined
$('#nextPage').hide();
function loadPage(pageNum, checkNextPage = false, sort_by = 'rank') {
    $('#loading').show();
    sort_by = lastClickedTab;

    $.ajax({
        url: '/get_landing_page/',
        type: 'GET',
        data: {
            'lang': 'en',
            'page_num': pageNum,
            'sort_by': sort_by
        },
        success: function(response) {
            $('#loading').hide();
            totalPages = response.num_wmc;
            totalPages = Math.ceil(totalPages / 5);
            //empty the pagination element
            $('#pagination').empty();
            var start = (currentSet - 1) *5 + 1;
            var end = Math.min(currentSet * 5, totalPages);
            // Populate the pagination with buttons
            for (var i = 1; i <= 5; i++) {
                var pageNumber = (currentSet - 1) * 5 + i;
                var link = $('<a>', {
                    text: pageNumber,
                    class: 'pagination-link',
                    href: '#',
                    'aria-label': GoToPage + pageNumber,
                    title: GoToPage + pageNumber
                });
                    link.click((function(pageNumber) {
                        return function(e) {
                            e.preventDefault(); //it always prevent the default action enabling to make the number disable when not available
                            if (!$(this).hasClass('disabled')){ 
                                currentPage = pageNumber;
                            loadPage(currentPage);
                            }    
                        };
                    })(pageNumber));  
                if (pageNumber > totalPages) {
                    //link.addClass('disabled');
                    link.hide();
                    //or change to link.hide() if you want to hide the number
                }
                $('#pagination').append(link);
            }    
            // Add a "Previous" button at the beginning
            var prevButton = $('<a>', {
                html: '<span class="arrow"><</span><span class="text">' + Back + '</span>',
                id: 'pagination-button-right',
                class: 'pagination-button flex-container',
                href: '#',
                'aria-label': GoToPrevious,
                title: GoToPrevious,
            });
            prevButton.on('click', function(e) {
                e.preventDefault(); // Always prevent the default action
                if (!$(this).hasClass('disabled') && currentSet > 1) {
                    currentSet--;
                    currentPage = (currentSet - 1) * 5 + 1;
                    loadPage(currentPage);
                }
            });
            if (currentSet == 1) {
                prevButton.addClass('disabled');
            }
            $('#pagination').prepend(prevButton);
            // Add a "Next" button at the end
            var nextButton = $('<a>', {
                html: '<span class="text">' + Next + '</span><span class="arrow">></span>',
                id: 'pagination-button-left',
                class: 'pagination-button flex-container',
                href: '#',
                'aria-label': GoToNext,
                title: GoToNext,
                click: function(e) {
                    e.preventDefault();
                    if (end < totalPages) {
                        currentSet++;
                        currentPage = (currentSet - 1) * 5 + 1;
                        loadPage(currentPage);
                    }
                }
            });

            if (end >= totalPages) {
                nextButton.addClass('disabled');
            }
            $('#pagination').append(nextButton);

            $('.pagination-link').removeClass('active');
            $('.pagination-link').eq(pageNum-start).addClass('active');

            if (checkNextPage) {
                if ($.trim(response.html) !== '') {
                    currentPage++;
                    loadPage(currentPage);
                }
            } else {
                $('.tile-wrapper.favourite-wmcs').html(response.html);
                if (pageNum == 1) {
                    //make the previous button disappear
                    $('#prevPage').fadeOut();
                } else {
                    $('#prevPage').fadeIn();
                }
            }
        },
        error: function(error) {
            console.log('Error:', error);
        }
    });
}

function nextPage() {
    // first check if the next page is empty.
    $('.tile-wrapper.favourite-wmcs').empty();
    loadPage(currentPage + 1, true);
    // Update the active class on the pagination links
    $('.pagination-link').removeClass('active');
    $('.pagination-link').eq(currentPage-1).addClass('active');

    currentSet = Math.ceil((currentPage +1)/5);
}

function prevPage() {
    if (currentPage > 1) {  // Prevent going to page 0 or negative
        currentPage--;
    $('.pagination-link').removeClass('active');
    $('.pagination-link').eq(currentPage-1).addClass('active');
    loadPage(currentPage);
    currentSet = Math.ceil((currentPage)/5);    
    }
}

$(document).ready(function() {
    var currentPage = 1;
    let timeout = null;
    var isSearchReset = false;
    // Add a keyup event handler for the search input
    $('#search-input').on('keyup', function(e) {
        var query = $(this).val();
        clearTimeout(timeout);
        // If the query is empty, restore the original HTML and return
        if (query === '') {
            if (!isSearchReset) { // Check if resetSearch has not been called yet
                resetSearch();
                isSearchReset = true; // Set the flag to true after resetting search
            }
            return false;
        } else {
            isSearchReset = false; // Reset the flag when the query is not empty
        }

        if (e.code === 'Space' || e.key === ' ' || e.code === 'Enter' || e.key === 'Enter') {
            // Perform the action immediately
            performSearch(query);
        } else {
            // Set a new timeout
            timeout = setTimeout(() => {
                // Function to call after 500 milliseconds of inactivity
                performSearch(query);
            }, 300); // 300 milliseconds delay
        }
    });

    function performSearch(query) {
        $('#prevPage, #nextPage, #pagination').hide(); // Hide the buttons and pagination
        $('#previousPage, #nextPages').fadeIn();
        $('.tablinks').prop('disabled', true); // Disable the tablinks
        // Call the AJAX function with page number 1
        ajaxCall(query, currentPage);
        $('.active').removeClass('active');
    }

    // Add click handlers for the previous and next buttons
    $('#previousPage').on('click', function(e) {
        e.preventDefault();
        var query = $('#search-input').val();
        if (currentPage > 1) {
            currentPage--;
            ajaxCall(query, currentPage);
        }
    });

    $('#nextPages').on('click', function(e) {
        e.preventDefault();
        var query = $('#search-input').val();
        currentPage++;
        ajaxCall(query, currentPage);
    });
});


//specially for the wmc searchbar in the landing_page.html
function ajaxCall(query, pageNum) {
    $.ajax({
        url: '/get_titles/',
        data: {
            'lang': 'en',
            'query': query,
            'page_num': pageNum
        },
        dataType: 'json',
        success: function (data) {
            $('#loading').hide();
            // Insert the search results into the #search-results div
            //check if the search results are empty
            if (data.html.trim() == ''){
                $('.tile-wrapper.favourite-wmcs').html(noResults);
                $('#previousPage, #nextPages').fadeOut();
                //$('.tablinks').show();
                currentPage = 1;
                return;
            } 
            $('.tile-wrapper.favourite-wmcs').html(data.html);

            // Check if the buttons already exist
            if ($('#previousPage').length === 0 && $('#nextPage').length === 0) {
                // Append the buttons only if they don't exist
                $('.tile-wrapper.favourite-wmcs').append('<button id="previousPage">Previous</button><button id="nextPage">Next</button>');
            }
            // Update the previous and next buttons
            $('#previousPage').prop('disabled', pageNum <= 1);
            $('#nextPages').prop('disabled', !data.has_next);
        },
        error: function (error) {
            console.error('Error:', error);
        }
    });
}

//the mostusedWMC tab is clicked by default and active. newWMC tab is notactive. When the newWMC tab is clicked, the mostusedWMC tab should be active and newWMC tab should be inactive.
$(document).ready(function() {
    $('#newWMC, #mostusedWMC').click(function() {
        $('#loading').show();
        $('.tile-wrapper.favourite-wmcs').empty();
        $('#newWMC, #mostusedWMC').removeClass('active').addClass('notactive');
        $(this).removeClass('notactive').addClass('active');
    });
});

function resetSearch() {
    loadPage(1, false, lastClickedTab);
    $('#previousPage, #nextPages').fadeOut();
    $('#prevPage, #nextPage, #pagination').show();
    $('.tablinks').show();
    currentPage = 1;

    $('.tablinks').removeClass('active');
    $('#' + activeTab).addClass('active');
    $('.tablinks').prop('disabled', false); // enable the tablinks if empty searchbar
}

$(document).ready(function() {
    // Function to show or hide the clear button
    function toggleClearButton() {
        if ($('#search-input').val() !== '') {
            $('#clear-input').show();
        } else {
            $('#clear-input').hide();
        }
    }
    // Initially hide the clear button
    toggleClearButton();
    // Show or hide the button when the user types in the input field
    $('#search-input').on('input', toggleClearButton);
    // Clear the input field and hide the button when it's clicked
    $('#clear-input').click(function() {
        $('#search-input').val('');
        $('.tablinks').prop('disabled', false);
        $(this).hide();  // Hide the button
        // If the query is empty, restore the original HTML and return
        if ($('#search-input').val() === '') {
            resetSearch();
            return false;
        }
    });
});

//if the user clicks search4AllWmc class in landing_page.html, the localStorage will be set to true
function setFilter() {
    localStorage.setItem('hideFilter', 'true');
}

$(document).ready(function() {
    // Attach the click event handler
    $('.search4AllWmc').click(setFilter);
});


$(document).ready(function(){
    resetSearchCatalogue("primary");
    startAutomaticSearch();

    if ($(window).width() < 689) {
        if(!$(".sidebar-wrapper").hasClass("closed")){
            $(".sidebar-toggler").click();
        }
    }

    // show and auto hide messages
    $(".messages-container").delay(500).slideToggle("medium");
    $(".messages-container").delay(5000).slideToggle("medium");
    rewrite_article_urls()
});

function rewrite_article_urls() {
    var currentURL = window.location.pathname,
    articlePattern = new RegExp('^/article/.*');

    if (articlePattern.test(currentURL)) {
        var anchors = document.getElementsByTagName('a');
        for (var i = 0; i < anchors.length; i++) {
            link=anchors[i].href;
            //console.log(link);
            if (link.includes("mediawiki/index.php") && !link.includes(".pdf") && !link.includes(".odt") ){
                var articleName = link.substr(link.lastIndexOf('/') + 1);
                var decoded = decodeURIComponent(articleName)
                var  wOutUmlaut = replaceUmlaute(decoded)
                anchors[i].href = location.protocol + "//" + location.hostname + "/mediawiki/" + wOutUmlaut
            } 
        }
    }
} 
const umlautMap = {
    '\u00dc': 'UE',
    '\u00c4': 'AE',
    '\u00d6': 'OE',
    '\u00fc': 'ue',
    '\u00e4': 'ae',
    '\u00f6': 'oe',
    '\u00df': 'ss',
    ':': '_',
  }

function replaceUmlaute(str) {
  return str
    .replace(/[\u00dc|\u00c4|\u00d6][a-z]/g, (a) => {
      const big = umlautMap[a.slice(0, 1)];
      return big.charAt(0) + big.charAt(1).toLowerCase() + a.slice(1);
    })
    .replace(new RegExp('['+Object.keys(umlautMap).join('|')+']',"g"),
      (a) => umlautMap[a]
    );
}

$(document).on("click", "#geoportal-empty-search-button", function(){
    document.getElementById("geoportal-search-field").value = '';
    document.getElementById("geoportal-empty-search-button").style.display = 'none';
    document.getElementById("geoportal-search-field").style.marginRight = '0px';
    $(".simple-search-autocomplete").hide();

});

/*
 * Scroll to Top Button
 */
function fadedHide () {
        // hide #backtotop
        $( "#backtotop" ).hide ();
        // fade in #backtotop
        $( function () {
                $( window ).scroll( function () {
                        if ( $( this ).scrollTop () > ButtonStart ) {
                                $( '#backtotop' ).fadeIn ();
                        } else {
                                $( '#backtotop' ).fadeOut ();
                        }
                });
        });
}

function goToTop (){
        $( 'body,html' ).animate ({
                scrollTop: 0
        }, ScrollSpeed );
        return false;
}

function addBackToTopButton () {
                $('<div id="backtotop" type="button" value=" " onClick="goToTop();"> </div>').appendTo('#mw-content');
                fadedHide ();
}

var ButtonStart = 50;
var ScrollSpeed = 600;

if( !window.BackToTop  ) {
        $( document ).ready( function () {
                addBackToTopButton ();
        });
}

/*
 * add badge to menu item NEWS if there is new content in the article Meldungen, keep the badge for 6 days
 */

function checkForNews (){
        const currentDate = new Date();
        const currentTimestamp = currentDate.getTime();
        url = location.origin + "/mediawiki/api.php?action=query&prop=revisions&rvlimit=1&rvprop=timestamp&rvdir=older&titles=Meldungen&format=json";
        fetch(url)
        .then(function(response){return response.json();})
        .then(function(response) {
                var pages = response.query.pages;
                for (var p in pages) {
                        articleDate = pages[p].revisions[0].timestamp;
                        articleDate = new Date(articleDate);
                        articleTimestamp = articleDate.getTime();
                }
                showIcon = (articleTimestamp + 86400000 * 6  >= currentTimestamp) ? true : false;
                if (showIcon == true) {
                         $('.menuMeldungen').append('<i class="fas fa-exclamation-circle" style="position: absolute;margin-left: 5px;color: var(--success-green);"></i>');
                }
        })
        .catch(function(error){console.log(error);});
}
var CheckForNewsPlaceIcon = true;
if( CheckForNewsPlaceIcon == true ) {
        $( document ).ready( function () {
          checkForNews();
        });
}

/*
 * reposition cookie-banner
*/
$(document).ready(function(){

    if($('.cookie-container-visible').length > 0){
        document.getElementById("main-body-class").style.margin = '143px 0px 0px 0px';
    }

    if ($(window).width() < 800) {
        if($('.cookie-container-visible').length > 0){
        document.getElementById("main-body-class").style.margin = '196px 0px 0px 0px';
        }
    }

    if($('.cookie-container-hidden').length > 0){
        document.getElementById("main-body-class").style.margin = 'unset';
    }
});

/*
 *  change pagetitle if mapviewer
*/
function changePageTitle() {
    newPageTitle = 'Geoportal Hessen - Kartenviewer';
    document.querySelector('title').textContent = newPageTitle;
}

function changePageTitleBack() {
    var url= window.location.href;
    var u1 = window.location.hostname;
    var urll= url.split('/');
    var urkl = urll[urll.length - 2] === u1 ? " Startseite" : "" + urll[urll.length - 2];
    if (urkl=== 'search'){
        newPageTitle = 'Geoportal Hessen ' + ' - ' + 'Suchergebnisse';
    } else{
        newPageTitle = 'Geoportal Hessen ' + ' - ' + urkl;
    } 
    document.querySelector('title').textContent = newPageTitle;
}
