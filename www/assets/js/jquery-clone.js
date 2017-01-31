/**
 * @author bala
 */

$('#add').click(function(){        
  $('#itemCounter').val(Number($('#itemCounter').val()) + 1);
  var newItem = $('div.item').first().clone();        
  childRecursive(newItem,            
      function(e){
          setCloneAttr(e, $('#itemCounter').val());
  });        
  childRecursive(newItem, 
      function(e){
          clearCloneValues(e);
  });        
  newItem.appendTo($('#items'));
});

// Accepts an element and a function
function childRecursive(element, func){
    // Applies that function to the given element.
    func(element);
    var children = element.children();
    if (children.length > 0) {
        children.each(function (){
            // Applies that function to all children recursively
            childRecursive($(this), func);
        });
    }
}

// Expects format to be xxx-#[-xxxx] (e.g. item-1 or item-1-name)
function getNewAttr(str, newNum){
    // Split on -
    var arr = str.split('-');
    // Change the 1 to wherever the incremented value is in your id
    arr[1] = newNum;
    // Smash it back together and return
    return arr.join('-');
}

// Written with Twitter Bootstrap form field structure in mind
// Checks for id, name, and for attributes.
function setCloneAttr(element, value){
    // Check to see if the element has an id attribute
    if (element.attr('id') !== undefined){
        // If so, increment it
        element.attr('id', getNewAttr(element.attr('id'),value));
    } else { /*If for some reason you want to handle an else, here you go */}
    // Do the same with name...
    if(element.attr('name') !== undefined){
        element.attr('name', getNewAttr(element.attr('name'),value));
    } else {}
    // And don't forget to show some love to your labels.
    if (element.attr('for') !== undefined){
        element.attr('for', getNewAttr(element.attr('for'),value));
    } else {}
}

// Sets an element's value to ''
function clearCloneValues(element){
    if (element.attr('value') !== undefined){
        element.val('');
    }
}