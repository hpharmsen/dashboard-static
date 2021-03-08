function onSignInLimited(googleUser) {
    onSignInLimited(googleUser,true)
}

function onSignIn(googleUser, limited=False) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.

	var myUserEntity = {};
  	myUserEntity.Id = profile.getId();
  	myUserEntity.Email = profile.getEmail();

  	//Store the entity object in sessionStorage where it will be accessible from all pages of your site.
  	sessionStorage.setItem('myUserEntity',JSON.stringify(myUserEntity));
	checkIfLoggedIn(limited);
}


function checkIfLoggedIn(limited) {
    return;
    if (window.location.hostname=='localhost')
        return; // local host is fine. No signin needed
    curpage = window.location.href.substring(window.location.href.lastIndexOf('/') + 1)
    if (sessionStorage.getItem('myUserEntity') == null) {
        // Redirect to login page, no user entity available in sessionStorage
	    if (curpage != 'login.html')
    	    window.location.href='login.html';
    } else {
  	    // User already logged in
	    var userEntity = {};
	    userEntity = JSON.parse(sessionStorage.getItem('myUserEntity'));
	    console.log('userEntity:',userEntity.Email);
		var allowed = ['hph@oberon.nl', 'rdb@oberon.nl', 'gert@oberon.nl', 'jellehoffenaar@gmail.com', 'annikawerk@gmail.com'];
		if (allowed.includes(userEntity.Email) || (limited && userEntity.Email.endsWidth('@oberon.nl'))) {
            var span = document.getElementById('user');
            if (span != undefined)
                span.textContent = userEntity.Email;
            if (curpage == 'login.html')
                window.location.href='dashboard.html';
        } else {
            //if (!limited) {
            //    alert( 'signing out because this is no limited page')
            //} else if (!userEntity.Email.endsWidth('@oberon.nl')) {
            //    alert( 'signing out because ' +userEntity.Email + ' does not end in @oberon.nl')
            //}
            //signOut()
        }
 	}
}

function onLoadAuth() {
    if (window.location.hostname=='localhost')
        return;
      gapi.load('auth2', function() {
        gapi.auth2.init();
      });
}


function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
		sessionStorage.removeItem('myUserEntity')
        console.log('User signed out.');
		checkIfLoggedIn();
    });
}

