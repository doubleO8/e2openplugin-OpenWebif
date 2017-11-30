# -*- coding: utf-8 -*-

##############################################################################
#                        2013 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
from twisted.web import resource

from Components.config import config as comp_config


def get_transcoding_features(encoder=0):
    features = {
        "automode": "automode",
        "bitrate": "bitrate",
        "framerate": "framerate",
        "resolution": "display_format",
        "aspectratio": "aspectratio",
        "audiocodec": "audio_codec",
        "videocodec": "video_codec",
        "gopframeb": "gop_frameb",
        "gopframep": "gop_framep",
        "level": "level",
        "profile": "profile",
        "width": "width",  # not in use
        "height": "height",  # not in use
    }
    encoder_features = {}
    for feature in features:
        if encoder == 0:
            if hasattr(comp_config.plugins.transcodingsetup, feature):
                try:
                    encoder_features[feature] = getattr(
                        comp_config.plugins.transcodingsetup, feature)
                except KeyError:
                    pass
        else:
            attr_name = "%s_%s" % (feature, encoder)
            if hasattr(comp_config.plugins.transcodingsetup, attr_name):
                try:
                    encoder_features[feature] = getattr(
                        comp_config.plugins.transcodingsetup, attr_name)
                except KeyError:
                    pass
    return encoder_features


ERROR_FMT = """
<?xml version="1.0" encoding="UTF-8" ?>
<e2simplexmlresult>
<e2state>false</e2state>
<e2statetext>{:s}</e2statetext></e2simplexmlresult>
"""


class TranscodingController(resource.Resource):
    def render(self, request):
        request.setHeader('Content-type', 'application/xhtml+xml')
        request.setHeader('charset', 'UTF-8')
        try:
            port = comp_config.plugins.transcodingsetup.port
        except KeyError:
            return ERROR_FMT.format('Transcoding Plugin is not installed or '
                                    'your STB does not support transcoding')

        encoders = (0, 1)
        if len(request.args):
            config_changed = False
            if "port" in request.args:
                new_port = request.args["port"][0]
                if new_port not in port.choices:
                    new_port = port.value
                if new_port != comp_config.plugins.transcodingsetup.port.value:
                    comp_config.plugins.transcodingsetup.port.value = new_port
                    config_changed = True
            encoder = 0
            if "encoder" in request.args:
                try:
                    encoder = int(request.args["encoder"][0])
                except ValueError:
                    return ERROR_FMT.format('wrong argument for encoder')
            encoder_features = get_transcoding_features(encoder)
            if not len(encoder_features):
                return ERROR_FMT.format('chosen encoder is not available')

            for arg in request.args:
                if arg in encoder_features:
                    attr = encoder_features[arg]
                    if hasattr(attr, "limits"):
                        try:
                            new_value = int(request.args[arg][0])
                        except ValueError:
                            response = 'wrong argument for {!r}'.format(arg)
                            return ERROR_FMT.format(response)

                        if new_value < int(attr.limits[0][0]):
                            new_value = int(attr.limits[0][0])
                        elif new_value > int(attr.limits[0][1]):
                            new_value = int(attr.limits[0][1])
                        if new_value != attr.value:
                            attr.value = new_value
                            config_changed = True
                    elif hasattr(attr, "choices"):
                        new_value = request.args[arg][0]
                        if new_value not in attr.choices:
                            response = 'wrong argument for {!r}'.format(arg)
                            return ERROR_FMT.format(response)
                        if new_value != attr.value:
                            attr.value = new_value
                            config_changed = True
                elif arg not in ("encoder", "port"):
                    response = 'chosen feature %s is not available'.format(arg)
                    return ERROR_FMT.format(response)
            if config_changed:
                comp_config.plugins.transcodingsetup.save()

        result = ['<?xml version="1.0" encoding="UTF-8" ?>',
                  '<e2configs>']

        for encoder in encoders:
            encoder_features = get_transcoding_features(encoder)
            if len(encoder_features):
                result.append("<encoder number=\"%s\">\n" % str(encoder))
            for arg in encoder_features:
                attr = encoder_features[arg]
                value = str(attr.value)
                if hasattr(attr, "limits"):
                    attr_min = str(attr.limits[0][0])
                    attr_max = str(attr.limits[0][1])
                    result.append('<e2config>')
                    result.append(
                        '<e2configname>{!s}</e2configname>'.format(arg))
                    result.append(
                        '<e2configlimits>{!s}-{!s}</e2configlimits>'.format(
                            attr_min, attr_max))
                    result.append(
                        '<e2configvalue>{!s}</e2configvalue>'.format(value))
                    result.append('</e2config>')
                elif hasattr(attr, "choices"):
                    chcs = ', '.join(attr.choices)
                    result.append('<e2config>')
                    result.append(
                        '<e2configname>{!s}</e2configname>'.format(arg))
                    result.append(
                        '<e2configchoices>{!s}</e2configchoices>'.format(chcs))
                    result.append(
                        '<e2configvalue>{!s}</e2configvalue>'.format(value))
                    result.append('</e2config>')
            if len(encoder_features):
                result.append('</encoder>')

        attr, arg = port, "port"
        value = str(attr.value)
        chcs = ', '.join(attr.choices)
        result.append('<e2config>')
        result.append(
            '<e2configname>{!s}</e2configname>'.format(arg))
        result.append(
            '<e2configchoices>{!s}</e2configchoices>'.format(chcs))
        result.append(
            '<e2configvalue>{!s}</e2configvalue>'.format(value))
        result.append('</e2config>')
        result.append('</e2configs>')

        return "\n".join(result)
