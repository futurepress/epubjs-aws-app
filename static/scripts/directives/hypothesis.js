'use strict';

/*
 * So the root issue here is that I hadn't thought that one would create an element
 * for the annotator themselves. I think of it more as a singleton service than a
 * directive. That's a little bit inconsistent with how Annotator upstream treats
 * the annotator (as a jQuery plugin, instantiated on any element). I tend to instantiate
 * it on the body element. This is reflected in how our embed typically exports
 * window.annotator rather than as upstream does $(anyElement).annotator() and instead
 * has window.Annotator._instances.
 *
 * I think there's room for a DOM-centric annotator API, but I'm leaning more toward
 * pushing things like element.annotations and bubbling events from where they happen.
 * That will make things like third-party, paragraph-level comments more sensibly webby.
 *
 * In that world, window.annotator is probably the entry point for the non-document
 * parts of the API. Things like requesting permissions to access the raw annotation
 * data (instead of stubs stripped of user data, as is exposed now) and single sign-on
 * APIs.
 *
 * If you agree and want to go down this route, the preemptive move would be to separate
 * this module into an angular service and a directive. You could export a service called
 * annotator which instantiates the Annotator.Host and returns it. The idea is that one
 * could, for instance, decide to check for window.annotator and export that, else load
 * us as a sort of polyfill for a future, browser-native annotator, or a user-deployed
 * extension. We should all be able to play nicely together if we get the core APIs
 * settled and documented.
 *
 * Then, the directive could inject the annotator, and its link function should be to
 * create the viewer/editor widget, instantiated upon the directive's element. Unfortunately,
 * the current Annotator has the editor/viewer as an assumed core component. In the short
 * term, I can give you an option at least for deciding where to put it. Probably the easiest
 * is for me to (finally) refactor our sidebar into a plugin which, like the toolbar, can take
 * a container option for where to attach.
 *
 * That the Annotator constructor takes an element as an argument I think is a hold-over of
 * the jQuery thinking of Annotator where one might instantiate any number of them on any
 * number of elements.
 *
 * All your thoughts welcome. If you could also e-mail me this comment, I would love to not
 * have to write it up again when I start bringing concrete proposals to Annotator devs.
 */

/*
 * Don't know if this is an exact response, but the annotator($element) vs var annotator = new Annotator()
 * is something that came up with the epubs. Ended up spliting it into the jquery way epub("path/to/book")
 * and the creating a object like var epub = new Epub() and then appending the pieces like 
 * epub.iframe.appendTo(element) which could work nicely in this situations.
 */

/*
 * That's along the lines of what I'm thinking.
 *
 * annotator = new Annotator()
 * annotator.viewer.appendTo(element)
 *
 * Although I think creating a viewer and an editor (and whether they're the same or
 * different widgets) is probably best made explicity, rather than implicit.
 */
angular.module('Reader')
	.directive('hypothesis', ['$window', function($window) {
		return {
			restrict: "E",
			scope: {
				src: '@',
				onAnnotationsLoaded: '&'
			},
			// templateUrl: '',

			controller: function($scope, $rootScope, $q){
				$scope.annotator = null;
			},

			link: function(scope, element, attrs) {
				scope.src = attrs.src;

				var setSinglePage = function (enabled) {
					scope.$parent.$apply(function () {
						scope.$parent.single = enabled;
					});
				}

        var body = $window.document.body;

				var annotator = window.annotator = new window.Annotator.Host(body, {
						"app": "https://hypothes.is/app/",
            "Toolbar": {container:"#singlepage"}
        });
        annotator.frame.appendTo(element);

				annotator.subscribe('annotationEditorShown', function () {
					setSinglePage(true);
					window.annotator.setVisibleHighlights(true)
				});
				annotator.subscribe('annotationViewerShown', function () {
					setSinglePage(true);
					window.annotator.setVisibleHighlights(true)
				});

				annotator.subscribe('annotationEditorHidden', function () {
					setSinglePage(false);
					//window.annotator.setVisibleHighlights(false)
				});
				annotator.subscribe('annotationViewerHidden', function () {
					setSinglePage(false);
					//window.annotator.setVisibleHighlights(false)
				});

				scope.annotator = annotator;

				scope.annotator.subscribe("annotationsLoaded", function(e){
					scope.onAnnotationsLoaded({ annotator: scope.annotator, annotations: e });
				});

			}

		}
	}]);
