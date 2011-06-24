# Copyright 2011 Citrix Systems.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from webob import exc

from quantum.api import api_common as common
from quantum.api import faults
from quantum.api.views import networks as networks_view
from quantum.common import exceptions as exception

LOG = logging.getLogger('quantum.api.networks')


class Controller(common.QuantumController):
    """ Network API controller for Quantum API """

    _network_ops_param_list = [{
        'param-name': 'network-name',
        'required': True}, ]

    _serialization_metadata = {
        "application/xml": {
            "attributes": {
                "network": ["id", "name"],
                "port": ["id", "state"],
            },
        },
    }

    def __init__(self, plugin_conf_file=None):
        self._resource_name = 'network'
        super(Controller, self).__init__()

    def index(self, request, tenant_id):
        """ Returns a list of network ids """
        #TODO: this should be for a given tenant!!!
        return self._items(request, tenant_id, net_detail=False)

    def _item(self, req, tenant_id, network_id,
              net_details, port_details):
        network = self.network_manager.get_network_details(
                            tenant_id, network_id)
        builder = networks_view.get_view_builder(req)
        result = builder.build(network, net_details, port_details)
        return dict(networks=result)

    def _items(self, req, tenant_id, net_details, port_details):
        """ Returns a list of networks. """
        networks = self.network_manager.get_all_networks(tenant_id)
        builder = networks_view.get_view_builder(req)
        result = [builder.build(network, net_details, port_details)['network']
                  for network in networks]
        return dict(networks=result)

    def show(self, request, tenant_id, id):
        """ Returns network details for the given network id """
        try:
            return self._item(request, tenant_id, id,
                              net_details=True, port_details=False)
        except exception.NetworkNotFound as e:
            return faults.Fault(faults.NetworkNotFound(e))

    def detail(self, request, **kwargs):
        tenant_id = kwargs.get('tenant_id')
        network_id = kwargs.get('id')
        try:
            if network_id:
                return self._item(request, tenant_id, network_id,
                                  net_details=True, port_details=True)
            else:
                #do like show but with detaik
                return self._items(request, tenant_id,
                                   net_details=True, port_details=False)
        except exception.NetworkNotFound as e:
            return faults.Fault(faults.NetworkNotFound(e))

    def create(self, request, tenant_id):
        """ Creates a new network for a given tenant """
        #look for network name in request
        try:
            request_params = \
                self._parse_request_params(request,
                                           self._network_ops_param_list)
        except exc.HTTPError as e:
            return faults.Fault(e)
        network = self.network_manager.\
                       create_network(tenant_id,
                                      request_params['network-name'])
        builder = networks_view.get_view_builder(request)
        result = builder.build(network)
        return dict(networks=result)

    def update(self, request, tenant_id, id):
        """ Updates the name for the network with the given id """
        try:
            request_params = \
                self._parse_request_params(request,
                                           self._network_ops_param_list)
        except exc.HTTPError as e:
            return faults.Fault(e)
        try:
            network = self.network_manager.rename_network(tenant_id,
                        id, request_params['network-name'])

            builder = networks_view.get_view_builder(request)
            result = builder.build(network, True)
            return dict(networks=result)
        except exception.NetworkNotFound as e:
            return faults.Fault(faults.NetworkNotFound(e))

    def delete(self, request, tenant_id, id):
        """ Destroys the network with the given id """
        try:
            self.network_manager.delete_network(tenant_id, id)
            return exc.HTTPAccepted()
        except exception.NetworkNotFound as e:
            return faults.Fault(faults.NetworkNotFound(e))
        except exception.NetworkInUse as e:
            return faults.Fault(faults.NetworkInUse(e))
