# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shop.rest.renderers import CMSPageRenderer


class ModifiedCMSPageRenderer(CMSPageRenderer):
    """
    Modified CMSPageRender to support rendering non CMS templates.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']
        template_context = self.get_template_context(dict(data), renderer_context)

        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)
            template_context['paginator'] = view.paginator
            if request.current_page:
                # set edit_mode, so that otherwise invisible placeholders can be edited inline
                template_context['edit_mode'] = request.current_page.publisher_is_draft

        template_context['data'] = data
        template_context.update(renderer_context)
        return template.render(template_context, request=request)
