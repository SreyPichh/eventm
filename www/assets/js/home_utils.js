var HomeApp = function() {

	var initCalender = function() {
		console.log('initializing initCalender');
		$('#calendar').fullCalendar({
				eventSources : [
				// your event source
				{
					events : [// put the array in the `events` property
					{
						title : 'event1',
						start : '2014-07-10'
					}, {
						title : 'event2',
						start : '2014-07-12',
						end : '2014-07-15'
					}, {
						title : 'event3',
						start : '2014-07-17T12:30:00',
					}],
					color : 'black', // an option!
					textColor : 'yellow' // an option!
				}, {
					events : [// put the array in the `events` property
					{
						title : 'tournament1',
						start : '2014-07-14',
						end : '2014-07-17'
					}, {
						title : 'tournament2',
						start : '2014-07-10T10:00:00',
						end : '2014-07-10T12:00:00',
					}],
					color : 'green', // an option!
					textColor : 'black' // an option!
				}]
			});

	};
	var initHScroll = function() {
		$('.hframe').each(function() {
			console.log('initializing initHScroll');
			$(this).sly({
				horizontal : 1,
				itemNav : 'basic',
				smart : 1,
				activateOn : 'click',
				mouseDragging : 0,
				touchDragging : 1,
				releaseSwing : 1,
				startAt : 0,
				scrollBar : $(this).parent().find('.hscrollbar'),
				scrollBy : 0,
				speed : 300,
				elasticBounds : 1,
				easing : 'easeOutExpo',
				dragHandle : 1,
				dynamicHandle : 0,
				clickBar : 1
			});
		});
	};
	// Handles scrollable contents using jQuery SlimScroll plugin.
	var initVScroll = function() {
		$('.scroller').each(function() {
			var height;
			if ($(this).attr("data-height")) {
				height = $(this).attr("data-height");
			} else {
				height = $(this).css('height');
			}
			$(this).slimScroll({
				size : '5px',
				color : ($(this).attr("data-handle-color") ? $(this).attr("data-handle-color") : 'rgba(0, 170, 255, 0.7)'),
				railColor : ($(this).attr("data-rail-color") ? $(this).attr("data-rail-color") : '#333'),
				position : 'right',
				height : height,
				alwaysVisible : ($(this).attr("data-always-visible") == "1" ? true : false),
				railVisible : ($(this).attr("data-rail-visible") == "1" ? true : false),
				disableFadeOut : true
			});
		});
	};
	var onePageScroll = function() {
		console.log('initializing one page scroll');
		$(".home-scroll").onepage_scroll({
			sectionContainer : ".section", // sectionContainer accepts any kind of selector in case you don't want to use section
			easing : "ease", // Easing options accepts the CSS3 easing animation such "ease", "linear", "ease-in",
			// "ease-out", "ease-in-out", or even cubic bezier value such as "cubic-bezier(0.175, 0.885, 0.420, 1.310)"
			animationTime : 1000, // AnimationTime let you define how long each section takes to animate
			pagination : true, // You can either show or hide the pagination. Toggle true for show, false for hide.
			updateURL : false, // Toggle this true if you want the URL to be updated automatically when the user scroll to each page.
			beforeMove : function(index) {
			}, // This option accepts a callback function. The function will be called before the page moves.
			afterMove : function(index) {
				console.log('moved');
			}, // This option accepts a callback function. The function will be called after the page moves.
			loop : false, // You can have the page loop back to the top/bottom when the user navigates at up/down on the first/last page.
			keyboard : true, // You can activate the keyboard controls
			responsiveFallback : '1200', // You can fallback to normal page scroll by defining the width of the browser in which
			// you want the responsive fallback to be triggered. For example, set this to 600 and whenever
			// the browser's width is less than 600, the fallback will kick in.
			direction : "vertical" // You can now define the direction of the One Page Scroll animation. Options available are "vertical" and "horizontal". The default value is "vertical".
		});
	};
	var fixSportsBar = function() {// this is the shorthand for document.ready
		$(document).scroll(function() {// this is the scroll event for the document
			console.log($("#sportsbar").position().top);
			scrolltop = $(document).scrollTop();
			// by this we get the value of the scrolltop ie how much scroll has been don by user
			console.log(scrolltop);
			if (parseInt(scrolltop) >= 400)// check if the scroll value is equal to the top of navigation
			{
				$('<li><a href="/phnom-penh">Select a sport <i class="fa fa-chevron-circle-down"></i></a></li>').appendTo('#home-navbar').show('slow');
				// is yes then make the position fixed to top 0
			} else {
				// is yes then make the position fixed to top 0
			}
		});
	};
	var initSearchMap = function() {
		google.maps.event.addDomListener(window, 'load', function() {
			center_geocode = [11.544872, 104.892166]; // Latlong values for Phnom Penh city
			//TODO: This to be replaced with retrieving the latlong for locality or respective city
			// Using the first latlong values from that page
			$('.formap').each(function () { 
				latlong_arr = $(this).find('.latlong').text().split(',');
			  //console.log('latlong, ' + latlong_arr)						
				center_geocode = [parseFloat(latlong_arr[0].trim()), parseFloat(latlong_arr[1].trim())]
			});
			console.log('locality center latlong, ' + center_geocode);
			var mapOptions = {
				center : new google.maps.LatLng(center_geocode[0], center_geocode[1]),
				zoom : 12
			};
			var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
			
			$('.formap').each(function () {
				pg = $(this).find('.name').text();
				latlong_arr = $(this).find('.latlong').text().split(',');
				//console.log('latlong for ' + pg + ' is ' + latlong_arr);
				geocode = new google.maps.LatLng(parseFloat(latlong_arr[0].trim()), parseFloat(latlong_arr[1].trim()));
				
				var marker = new google.maps.Marker({
				    position: geocode,
				    title:pg,
				    map: map
				});
				
			});
		});
	};

	var initDetailsMap = function() {
		google.maps.event.addDomListener(window, 'load', function() {
			center_geocode = [11.544872, 104.892166]; // Latlong values for Phnom Penh city
			name = '';
			$('.formap').each(function () {
				name = $(this).find('.name').text();
				latlong_arr = $(this).find('.latlong').text().split(',');
				//console.log('latlong for ' + pg + ' is ' + latlong_arr);
				center_geocode = [parseFloat(latlong_arr[0].trim()), parseFloat(latlong_arr[1].trim())]
			});
			var geocode = new google.maps.LatLng(center_geocode[0], center_geocode[1]);
			console.log('initDetailsMap: locality center latlong, ' + center_geocode);						
			var mapOptions = {
				center : geocode,
				zoom : 14
			};
			var map = new google.maps.Map(document.getElementById("details-map"), mapOptions);
			var marker = new google.maps.Marker({
		    position: geocode,
		    title : name,
		    map: map
			});
		});
	};
	
	var hideAlert = function() {
		console.log('going to hide alert');
		$("#alert").delay(3000).fadeOut(300);
		console.log('alert hidden');
	};
	
	var geoBounds = function() {
		var southWest = new google.maps.LatLng( 11.6166667, 102.9666667 );
		var northEast = new google.maps.LatLng(12.4666667, 106.0166667 );
		var chennaiBounds = new google.maps.LatLngBounds( southWest, northEast );
					
		var options = {
		  bounds: chennaiBounds,
		  types: ['(regions)'],
			componentRestrictions: {country: "KH"}
		};
		$("#nav-locality").geocomplete(options)
    	.bind("geocode:result", function(event, result){
      	$("#nav-locality_id").val(result.place_id);
      	$("#nav-locality").val(result.name);
    });
		$("#pg-locality,#tc-locality,#se-locality").geocomplete(options)
    	.bind("geocode:result", function(event, result){
      	$("#pg-locality_id,#tc-locality_id,#se-locality_id").val(result.place_id);
      	$("#pg-locality,#tc-locality,#se-locality").val(result.name);
    });
    $("#address-locality").geocomplete(options)
    	.bind("geocode:result", function(event, result){        	
      	$("#locality_id").val(result.place_id);
      	$("#address-locality").val(result.name);
    });
    $("#address-city").geocomplete(options)
    	.bind("geocode:result", function(event, result){    	
      	$("#address-city").val(result.name);
    });
    $("#locality").geocomplete(options)
    	.bind("geocode:result", function(event, result){
      	$("#locality_id").val(result.place_id);
      	$("#locality").val(result.name);
    });
    $("#city").geocomplete(options)
    	.bind("geocode:result", function(event, result){
      	$("#city").val(result.name);
    });
	};
	
	var initEnquire = function() {
		$("#enquire_form").validate({        
		  rules: {
		      enq_date: "required",
		      enq_time: "required"
		  },        
		  
		  messages: {
		      enq_date: "Please select your favorite date",
		      enq_time: "Please select your favorite time"	            
		  },
		  
		  errorPlacement: function(error, element) {            
		      error.css({'color':'#FF4000'});            
		  		error.insertAfter(element);
		  },
		  
		  submitHandler: function(form) {
		      form.submit();
		  }
		});
	};

	//13.0524139, 80.2508246
	
	return {

		//main function to initiate the theme
		initHome : function() {
			hideAlert();
			initHScroll();
			initVScroll();
			//fixSportsBar();
			// handles slim scrolling contents
			//onePageScroll();
			geoBounds();
		},
		initDetails : function() {
			hideAlert();
			//initHScroll();
			initVScroll();
			initDetailsMap();
			//initCalender();
			geoBounds();
			initEnquire();
		},
		initSearch : function() {
			hideAlert();
			//initHScroll();
			initVScroll();
			initSearchMap();
			//initCalender();
			geoBounds();
		},
		initDashboard : function() {
			initVScroll();
			hideAlert();
			geoBounds();
		}
	};
}();

// below scripts added by senthil //
// for ckeditor customized toolbar script //
Custom =
[
	{ name: 'basicstyles', items : [ 'Bold','Italic','-','RemoveFormat' ] },
	{ name: 'paragraph', items : [ 'NumberedList','BulletedList','-','Outdent','Indent' ] },
	{ name: 'styles', items : [ 'Styles','Format' ] },
	{ name: 'colors', items : [ 'TextColor','BGColor' ] },
	{ name: 'links', items : [ 'Link','Unlink' ] },		
	{ name: 'clipboard', items: [ 'Undo', 'Redo' ] },
	{ name: 'document', items: [ 'Source' ] },
];

/*CKEDITOR.replace( 'description',
{
	toolbar : Custom,
	//uiColor : '#666666'
});*/

$.getScript('//cdnjs.cloudflare.com/ajax/libs/summernote/0.5.1/summernote.min.js',function(){
  $('.summernote').summernote({
  	toolbar: [
        ['style', ['style', 'bold', 'italic', 'underline', 'clear']],            
        ['para', ['ul', 'ol', 'paragraph']],            
        ['table', ['table']],
        ['insert', ['link', 'picture']],
        ['view', ['fullscreen', 'codeview', 'help']]
    ],
     height:150         
  });  
});
		
// for tab toggle from button click and url //
// active tab where nav entry from url //
var activeTab = $('[href=' + location.hash + ']');
activeTab && activeTab.tab('show');

$('a[data-toggle="tab"]').on('show.bs.tab', function (e) {	
  // add active class where nav entry is active //
  $('.nav a[data-toggle="tab"][href="'+$(e.target).attr("href")+'"]')
    .parent().addClass('active');

  // remove active class where nav entry is no longer active //
  $('.nav a[data-toggle="tab"][href!="'+$(e.target).attr("href")+'"]')
    .parent().removeClass('active');		
});

// for form fields lable //
//$("table th").addClass("text-right plr10");
$('#new_player').attr('type', 'none');
$('label[for=new_player-0]').remove();
$('#media').attr('type', 'none');
$('label[for=media-0]').remove();

// for google search api script //
/*var HomeApp = function() {
	var southWest = new google.maps.LatLng( 12.5950, 80.1525 );
	var northEast = new google.maps.LatLng( 13.0300, 80.1504 );
	var chennaiBounds = new google.maps.LatLngBounds( southWest, northEast );
				
	var options = {
	  bounds: chennaiBounds,
	  types: ['(regions)'],
		componentRestrictions: {country: "KH"}
	};
};*/
