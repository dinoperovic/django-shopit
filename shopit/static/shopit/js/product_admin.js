var jQuery = window.jQuery || django.jQuery;

(function ($) {
  'use strict';

  var isNew;

  var attributeValues = function () {
    var $attributeValues = $('#attribute_values-group');

    var attributeChoicesUrl = isNew ? '../' : '../../';
    attributeChoicesUrl += 'get-attribute-choices/';

    // Show correct choices for the choice field.
    var showCorrectChoices = function ($row) {
      var $select = $row.find('.field-choice select');
      var $attribute = $row.find('.field-attribute select');
      var selectedValue = parseInt($select.find('option:selected').val(), 10);

      $.get(attributeChoicesUrl, {'attribute_id': $attribute.val()}, function (data) {
        $select.html('');
        var hasSelected = false;
        $.each(data.choices, function (index, choice) {
          choice.id = (choice.id === null) ? '' : choice.id;
          var $option = $('<option value="'+ choice.id +'">'+ choice.label +'</option>');
          if (choice.id === selectedValue) { $option.prop('selected', true); hasSelected = true; }
          $select.append($option);
        });
        if (!hasSelected) { $select.find('option:first').prop('selected', true); }
        $select.trigger('change');
      });
    };

    // Init each row, and listen on attribute change.
    $attributeValues.find('.form-row').each(function () {
      showCorrectChoices($(this));
    });

    $(document).on('change', '.form-row .field-attribute select', function (event) {
      var $row = $(event.target).parent().parent().parent();
      showCorrectChoices($row);
    });
  };

  $(document).ready(function () {
    isNew = $('#content .viewsitelink').length === 0;
    attributeValues();
  });
})(jQuery);
