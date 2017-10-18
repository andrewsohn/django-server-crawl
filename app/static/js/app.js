;
(function($, window, document, undefined) {
	'use strict';

	// namespace
	var app = app || {};
	app.ui = app.ui || {};

	app.ui.Main = (function() {
		var _defaults = {
			content: '.content',
			sform: '.settig-form',
			// doCrawlUrl: '/api/test/',
			getCrawlUrl: '/crawl/',
			doCrawlUrl: '/crawl/save/',
			autoplaySpeed: 2000,
			speed: 2000,
			fade: true
        };

		return {
			init: function(container, options) {
				this._options = $.extend(true, _defaults, options);
                this._body = container;
                
                this._assignedHTMLElements();
                this._initProperties();
                this._attachEvents();
                this._initValidate();
			},
			_assignedHTMLElements: function() {
				this.$content = this._body.find(this._options.content);
				this.$sform = this.$content.find(this._options.sform);
				console.log(this.$sform)
			},
			_initProperties: function() {
				var _this = this;

				$.ajax({
					url : _this._options.getCrawlUrl
					, cache : false
					, type : 'GET'
					, data : {}
					, contentType : "application/json; charset=utf-8"
					, dataType: "json"
					, beforeSend : function (xhr) {
						xhr.setRequestHeader ("Accept", 'application/json; indent=4');
						xhr.setRequestHeader ("Authorization", "Basic " + btoa('admin:wlsrhkd2'));
					}
				}).fail(function() {
					alert('데이터 통신 중 오류가 발생했습니다.');
				}).done(function(result) {
					if (!result) return;
					console.log(result);
				});
			},
			_attachEvents: function() {
				this.$sform.submit(function(e) { e.preventDefault(); });
			},
			_initValidate: function() {
				if (!this.$sform.size()) return;
				
				this.$sform.validate({
					onclick : false, onfocusout : false, onkeyup : false, focusInvalid : false
					, rules : {
						sns_kind : 'required'
					}
					, messages : {
						sns_kind : { required : 'SNS를 선택하세요' }
					}
					, errorPlacement: function(error, element) {
						return false; 
					}
					, showErrors : $.proxy(this._errorHandle, this)
					, submitHandler : $.proxy(this._sformSubmit, this)
				});
			},
			_errorHandle : function(msgs, errs) {		
				if (!errs.length) return;
				
				alert(errs[0].message);
				$(errs[0].element).trigger('focus');
			},
			_sformSubmit: function(e) {
				var formArray = this.$sform.serializeArray();
				var jsonData = {};
				var _this = this; 

				for (var i = 0; i < formArray.length; i++){
					jsonData[formArray[i]['name']] = formArray[i]['value'];
				}

				console.log(jsonData);

				// jsonData['username'] = 'admin';
				// jsonData['password'] = 'wlsrhkd2';

				$.ajax({
					url : _this._options.doCrawlUrl
					, cache : false
					, type : 'GET'
					, data : jsonData
					, contentType : "application/json; charset=utf-8"
					, dataType: "json"
					, beforeSend : function (xhr) {
						xhr.setRequestHeader ("Accept", 'application/json; indent=4');
						xhr.setRequestHeader ("Authorization", "Basic " + btoa('admin:wlsrhkd2'));
					}
				}).fail(function() {
					alert('데이터 통신 중 오류가 발생했습니다.');
				}).done(function(result) {
					if (!result) return;
					console.log(result);
				});
				
				// e.submit();
			}
		};
	})();

	$(function() {
		console.log('ok');
		var body = $('body');
		app.ui.Main.init(body, {
			'test':'test'
		});
	});
})(jQuery, window, document);