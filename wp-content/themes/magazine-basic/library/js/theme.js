( function( $ ) {
	// Responsive videos
	var all_videos = $( '.entry-content' ).find( 'iframe[src*="player.vimeo.com"], iframe[src*="youtube.com"], iframe[src*="youtube-nocookie.com"], iframe[src*="dailymotion.com"],iframe[src*="kickstarter.com"][src*="video.html"], object, embed' );

	all_videos = all_videos.not( 'object object' );

	all_videos.each( function() {
		var video = $(this);

		if ( video.parents( 'object' ).length )
			return;

		if ( ! video.prop( 'id' ) )
			video.attr( 'id', 'rvw' + Math.floor( Math.random() * 999999 ) );

		video
			.wrap( '<div class="responsive-video-wrapper" style="padding-top: ' + ( video.attr( 'height' ) / video.attr( 'width' ) * 100 ) + '%" />' )
			.removeAttr( 'height' )
			.removeAttr( 'width' );
	} );

	// Mobile menu
	$( '#header' ).on( 'click', '#mobile-menu a', function() {
		if ( $(this).hasClass( 'left-menu' ) )
			$( '#nav-wrapper' ).toggleClass( 'menu-open' );
		else
			$( '#drop-down-search' ).slideToggle( 'fast' );
	} );

	// Open submenus in mobile menu
	$( '#nav-wrapper' ).on( 'click', '.sub-menu-parent > a', function(e) {
		e.preventDefault();

		if ( $(this).parents( '#nav-wrapper' ).hasClass( 'menu-open' ) )
			$(this).toggleClass( 'open' ).parent().find( '.sub-menu:first' ).toggle();
	} );

	// Image anchor
	$( 'a:has(img)' ).addClass( 'image-anchor' );
} )( jQuery );