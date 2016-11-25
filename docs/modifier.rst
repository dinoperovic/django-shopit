Modifier
########

Modifiers allow you to create different cart and cart item modifications
on a specific set of **Products**. You can assign them to any **Categorization** model and to a **Product**.

----

There are 3 kind of **Modifiers**:

* ``STANDARD`` affects the product regardles. Usefull for taxing specific set of products.
* ``DISCOUNT`` checks for a "Discountable" flag on a product and should be negative.
* ``CART`` will affect an entire cart.

Modifiers allow you set either the amount or the percentage with what the price will be modified.
Those values should be negative when creating discounts.

Modifier Conditions
===================

Conditions can be created for a modifier that then must be met to make the modifier valid.
You can use the default ones, or create custom conditions.

Default conditions
------------------

**Shopit** comes with a couple of simple conditions available for use.
When creating a **Modifier** in admin, you'll get to choose from:

* ``PriceGreaterThanCondition``
* ``PriceLessThanCondition``
* ``QuantityGreaterThanCondition``
* ``QuantityLessThanCondition``

They all accept a value. Quantity conditions control only modifiers on cart items.

Create custom conditions
------------------------

To create a custom conditions you must extend from :class:`shopit.modifier_conditions.ModifierCondition` and then
you can implement methods ``cart_item_condition`` and ``cart_condition``. They both accept an optional ``value``
argument as decimal number that can be passed in when selecting the condition.

.. code:: python

    from datetime import datetime

    from shopit.modifier_conditions import ModifierCondition


    class DayIsOddCondition(ModifierCondition):
        name = 'Day is odd'

        def cart_item_condition(self, request, cart_item, value=None):
            return self.day_is_odd()

        def cart_condition(self, request, cart, value=None):
            return self.day_is_odd()

        def day_is_odd(self):
            return datetime.today().day % 2 == 1


Now with the condition above, when selected on a modifier it will only be active when the day is odd.
Since both methods ``cart_item_condition`` and ``cart_condition`` are overriden, the condition will control the
modifier in cases both when it's applied to a cart item, or an entire cart. By default when not overriden those methods
return ``True``.

Last thing do to is add the path to your condition to ``SHOPIT_MODIFIER_CONDITIONS`` list.

.. code:: python

    SHOPIT_MODIFIER_CONDITIONS = [
        'shopit.modifier_conditions.PriceGreaterThanCondition',
        'shopit.modifier_conditions.PriceLessThanCondition',
        'shopit.modifier_conditions.QuantityGreaterThanCondition',
        'shopit.modifier_conditions.QuantityLessThanCondition',
        'myapp.modifier_conditions.DayIsOddCondition',
    ]


Discount codes
==============

Other than conditions, modifiers can be limited to a set of discount codes that makes them valid.
To achive that you need to create a ``DiscountCode`` and assign it to a modifier. When active discount codes exist
on a modifier, it is no longer active without one of those codes applied to the cart.

Discount codes can also be limited for the specific customer to use only.


