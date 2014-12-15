# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2014 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

"""
===========
Description
===========

This module defines the GraphManager which interacts between graph elements and
the DB.

Functional
==========

The role of the GraphManager is to ease graph element CRUD operations and
to retrieve graphs, vertices and edges thanks to methods with all element
parameters useful to find them.

This last could be specialized in assigning the GRAPH_TYPE class attribute to a
dedicated Graph type.

All methods may have to be enough generics without the need to override them,
the business code is ensured by graph elements.

Technical
=========

The graph manager permits to get graph elements with any context information.

First, generic methods permit to get/put/delete elements in understanding such
elements such as dictionaries.

Two, it is possible to find graphs, vertices and edges thanks to parameters
which correspond to their properties.
"""

from canopsis.common.init import basestring
from canopsis.configuration.configurable.decorator import (
    conf_paths, add_category
)
from canopsis.middleware.registry import MiddlewareRegistry
from canopsis.graph.elements import Graph, Edge, GraphElement, Vertice

CONF_PATH = 'graph/graph.conf'
CATEGORY = 'GRAPH'


@add_category(CATEGORY)
@conf_paths(CONF_PATH)
class GraphManager(MiddlewareRegistry):
    """
    Manage graph data in using a graph type which choose how to deserialize
    graph elements.
    """

    STORAGE = 'graph_storage'  #: graph storage name

    GRAPH_TYPE = Graph  #: default graph type

    def get_elts(
        self,
        ids=None, types=None, graph_ids=None, data=None, base_type=None,
        query=None
    ):
        """
        Get graph element(s) related to input ids, types and query.

        :param ids: list of ids or id of element to retrieve. If None, get all
            elements. If str, get one element.
        :type ids: list or str
        :param types: graph element types to retrieve.
        :type types: list or str
        :param graph_ids: graph ids from where find elts.
        :type graph_ids: list or str
        :param data: data query
        :param dict query: element search query.
        :param str base_type: elt base type.

        :return: element(s) corresponding to input ids and query.
        :rtype: list or dict
        """

        # init query if None
        if query is None:
            query = {}
        # put base type in query
        if base_type is not None:
            query[GraphElement.BASE_TYPE] = base_type
        # put types in query if not None
        if types is not None:
            if not isinstance(types, basestring):
                types = {'$in': types}
            query[GraphElement.TYPE] = types
        # put data if not None
        if data is not None:
            if isinstance(data, dict):
                for name in data:
                    data_name = 'data.{0}'.format(name)
                    query[data_name] = data[name]
            else:
                query[Vertice.DATA] = data
        # find ids among graphs
        if graph_ids is not None:
            result = []
            graphs = self.get_elts(ids=graph_ids)
            if graphs is not None:
                # all graph elt ids
                elt_ids = set()
                # ensure graphs is a list of graphs
                if isinstance(graphs, dict):
                    graphs = [graphs]
                for graph in graphs:
                    if Graph.ELTS in graph:
                        elts = set(graph[Graph.ELTS])
                        elt_ids |= elts
                # if ids is not given, use elt_ids
                if ids is None:
                    ids = list(elt_ids)
                else:  # else use jonction of elt_ids and ids
                    if isinstance(ids, basestring):
                        ids = [ids]
                    ids = list(elt_ids & set(ids))

        # get elements with ids and query
        result = self[GraphManager.STORAGE].get_elements(ids=ids, query=query)

        return result

    def del_elts(self, ids=None, types=None, query=None, cache=False):
        """
        Del elements identified by input ids in removing reference before.

        :param ids: list of ids or id elements to delete. If None, delete all
            elements.
        :type ids: list or str
        :param types: element types to delete.
        :type types: list or str
        :param dict query: additional deletion query.
        :param bool cache: use query cache if True (False by default).
        """

        # initialize query if None
        if query is None:
            query = {}
        # put types in query
        if types is not None:
            query[GraphElement.TYPE] = types
        # remove references in graph
        self.remove_elts(ids=ids, cache=cache)
        # remove edge references
        self.del_edge_refs(vids=ids, cache=cache)
        # remove elements
        self[GraphManager.STORAGE].remove_elements(
            ids=ids, _filter=query, cache=cache
        )

    def put_elt(self, elt, graph_ids=None, cache=False):
        """
        Put an element.

        :param dict elt: element to put.
        :type elt: dict or GraphElement
        :param str graph_ids: element graph id. None if elt is a graph.
        :param bool cache: use query cache if True (False by default).
        """

        # ensure elt is a dict
        if isinstance(elt, GraphElement):
            elt = elt.to_dict()
        elt_id = elt[GraphElement.ID]

        # put elt value in storage
        self[GraphManager.STORAGE].put_element(
            _id=elt_id, element=elt, cache=cache
        )
        # update graph if graph_id is not None
        if graph_ids is not None:
            graphs = self.get_graphs(ids=graph_ids)
            if graphs is not None:
                # ensure graphs is a list of graphs
                if isinstance(graphs, Graph):
                    graphs = [graphs]
                for graph in graphs:
                    # if graph exists and elt_id not already present
                    if elt_id not in graph.elts:
                        # add elt_id in graph elts
                        graph.elts.append(elt_id)
                        graph.save(self, cache=cache)

    def remove_elts(self, ids, graph_ids=None, cache=False):
        """
        Remove vertices from graphs.

        :param ids: elt ids to remove from graph_ids.
        :type ids: list or str
        :param graph_ids: graph ids from where remove self.
        :type graph_ids: list or str
        :param bool cache: use query cache if True (False by default).
        """

        # get graphs in order to remove references to self from them
        graphs = self.get_graphs(ids=graph_ids, elts=ids)
        if graphs is not None:
            # ensure graps is a list
            if isinstance(graphs, Graph):
                graphs = [graphs]
            if ids is None:
                ids = []
            elif isinstance(ids, basestring):
                ids = [ids]
            for graph in graphs:
                for _id in ids:
                    if _id in graph.elts:
                        # remove elf from graph.elts
                        graph.remove_elts(_id)
                        # save the graph
                        graph.save(manager=self, cache=cache)

    def del_edge_refs(
        self, ids=None, vids=None, sources=None, targets=None, cache=False
    ):
        """
        Delete references of vertices from edges.

        :param ids: edge ids to select for removing vertices links.
        :type ids: list or str
        :param vids: vertice ids to remove from edge links.
        :type vids: list or str
        :param sources: source ids to remove.
        :type sources: list or str
        :param targets: target ids to remove.
        :type targets: list or str
        :param bool cache: use query cache if True (False by default).
        """

        edges = self.get_edges(ids=ids, sources=sources, targets=targets)

        if edges is not None:
            # ensure edges is a list
            if isinstance(edges, basestring):
                edges = [edges]
            # for all edges
            for edge in edges:
                # del refs
                edge.del_refs(ids=vids, sources=sources, targets=targets)
                # and save them
                edge.save(manager=self, cache=cache)

    def get_graphs(
        self, ids=None, types=None, elts=None, graph_ids=None, data=None,
        query=None,
        add_elts=False
    ):
        """
        Get one or more graphs related to input ids, types and elts.

        :param ids: graph ids to retrieve.
        :type ids: list or str
        :param types: graph types to retrieve.
        :type types: list or str
        :param elts: elts embedded by graphs to retrieve.
        :type elts: list or str
        :param graph_ids: graph ids from where get graphs.
        :type graph_ids: list or str
        :param data: data to find among graphs.
        :param dict query: additional graph search query. Could help to search
            specific data information.
        :param bool add_elts: (False by default) add elts in the result.

        :return: graph(s) corresponding to input parameters.
        :rtype: list or Graph
        """

        result = []
        # init query
        if query is None:
            query = {}
        # put elts in query
        if elts is not None:
            if not isinstance(elts, basestring):
                elts = {'$in': elts}
            query[Graph.ELTS] = elts
        # get graphs with ids and query
        graphs = self.get_elts(
            ids=ids,
            query=query,
            types=types,
            graph_ids=graph_ids,
            data=data,
            base_type=Graph.BASE_TYPE
        )
        # check if result may one graph or a list
        unique = False
        # if add_elts is asked
        if graphs is not None:
            # if graphs is unique, graphs is a dict
            if isinstance(graphs, dict):
                # set unique value to True
                unique = True
                # put graphs in a list
                graphs = [graphs]
            # save new_element method for quick resolution
            new_element = GraphElement.new_element
            # iterate on graphs
            for graph in graphs:
                try:
                    new_graph = new_element(**graph)
                    # if add elts, find them and add them into the graph
                    if add_elts:
                        # fill the graph with
                        new_graph.update_gelts(manager=self)
                    result.append(new_graph)
                except TypeError as te:
                    self.logger.warning(
                        'element {0} is not a graph. {1}'.format(graph, te)
                    )
        # get the first element if unique
        if unique:
            result = result[0] if result else None

        return result

    def get_targets(
        self,
        ids=None, graph_ids=None,
        data=None, query=None,
        types=None, edge_ids=None, add_edges=False, edge_types=None,
        edge_data=None, edge_query=None
    ):
        """
        Ease the use of get_neighbourhood method in order to get targets
            vertices.
        """

        return self.get_neighbourhood(
            ids=ids, graph_ids=graph_ids, sources=False, targets=True,
            target_data=data, target_query=query, target_types=types,
            edge_ids=edge_ids, add_edges=add_edges,
            target_edge_types=edge_types, target_edge_data=edge_data,
            target_edge_query=edge_query
        )

    def get_sources(
        self,
        ids=None, graph_ids=None,
        data=None, query=None,
        types=None, edge_ids=None, add_edges=False, edge_types=None,
        edge_data=None, edge_query=None
    ):
        """
        Ease the use of get_neighbourhood method in order to get sources
            vertices.
        """

        return self.get_neighbourhood(
            ids=ids, graph_ids=graph_ids, sources=True, targets=False,
            source_data=data, source_query=query, source_types=types,
            edge_ids=edge_ids, add_edges=add_edges,
            source_edge_types=edge_types, source_edge_data=edge_data,
            source_edge_query=edge_query
        )

    def get_neighbourhood(
        self,
        ids=None, sources=False, targets=True,
        graph_ids=None,
        data=None, source_data=None, target_data=None,
        types=None, source_types=None, target_types=None,
        edge_ids=None, edge_types=None, add_edges=False,
        source_edge_types=None, target_edge_types=None,
        edge_data=None, source_edge_data=None, target_edge_data=None,
        query=None, edge_query=None, source_query=None, target_query=None
    ):
        """
        Get neighbour vertices identified by context parameters.

        Sources and targets are handled in not directed edges.

        :param ids: vertice ids from where get neighbours.
        :type ids: list or str
        :param bool sources: if True (False by default) add source vertices.
        :param bool targets: if True (default) add target vertices.
        :param graph_ids: vertice graph ids.
        :type graph_ids: list or str
        :param dict data: neighbourhood data to find.
        :param dict source_data: source neighbourhood data to find.
        :param dict target_data: target neighbourhood data to find.
        :param types: vertice type(s).
        :type types: list or str
        :param types: neighbourhood types to retrieve.
        :type types: list or str
        :param source_types: neighbourhood source types to retrieve.
        :type source_types: list or str
        :param target_types: neighbourhood target types to retrieve.
        :type target_types: list or str
        :param edge_ids: edge from where find target/source vertices.
        :type edge_ids: list or str
        :param edge_types: edge types from where find target/source vertices.
        :type edge_types: list or str
        :param bool add_edges: if True (default), add pathed edges in the
            result.
        :param source_edge_types: edge types from where find source vertices.
        :type source_edge_types: list or str
        :param target_edge_types: edge types from where find target vertices.
        :type target_edge_types: list or str
        :param dict edge_data: edge data to find.
        :param dict source_edge_data: source edge data to find.
        :param dict target_edge_data: target edge data to find.
        :param dict query: additional search query.
        :param dict edge_query: additional edge query.
        :param dict source_query: additional source query.
        :param dict target_query: additional target query.
        :return: list of neighbour vertices designed by ids, or dict of
            {edge: list(vertices)} if add_edges.
        :rtype: list or dict
        """

        result = {} if add_edges else []

        # init types
        if isinstance(types, basestring):
            types = [types]

        # init edges
        edges = set()

        # search among source edges even if not sources because
        # edges can be not directed
        # init source_types
        if source_types is not None:
            if isinstance(source_types, basestring):
                source_types = [source_types]
        if types is not None:
            source_types += types
        # init source query
        if source_query is not None:
            if query is not None:
                source_query.update(query)
        else:
            source_query = query
        # init source edge types
        if source_edge_types is not None:
            if isinstance(source_edge_types, basestring):
                source_edge_types = [source_edge_types]
            if edge_types is not None:
                if isinstance(edge_types, basestring):
                    source_edge_types.append(edge_types)
                else:
                    source_edge_types += edge_types
        else:
            source_edge_types = edge_types
        # init source edge data
        if source_edge_data is not None:
            if edge_data is not None:
                source_edge_data.update(edge_data)
            else:
                source_edge_data = edge_data
        # get all source edges
        source_edges = self.get_edges(
            ids=edge_ids,
            graph_ids=graph_ids,
            types=source_edge_types,
            targets=ids,
            data=source_edge_data,
            query=source_query
        )
        # fill edges
        if source_edges is not None:
            # if source_edges is an edge
            if isinstance(source_edges, Edge):
                # and sources or source_edges is not directed
                if sources or not source_edges.directed:
                    edges.add(source_edges)
            elif sources:  # if sources
                edges |= set(source_edges)
            else:
                for source_edge in source_edges:
                    # add not directed edges
                    if not source_edge.directed:
                        edges.add(source_edge)

        # search among target edges
        # init target types
        if target_types is not None:
            if isinstance(target_types, basestring):
                target_types = [target_types]
        if types is not None:
            target_types += types
        # init target query
        if target_query is not None:
            if query is not None:
                target_query.update(query)
        else:
            target_query = query
        # init target edge types
        if target_edge_types is not None:
            if isinstance(target_edge_types, basestring):
                target_edge_types = [target_edge_types]
            if edge_types is not None:
                if isinstance(edge_types, basestring):
                    target_edge_types.append(edge_types)
                else:
                    target_edge_types += edge_types
        else:
            target_edge_types = edge_types
        # init target edge data
        if target_edge_data is not None:
            if edge_data is not None:
                target_edge_data.update(edge_data)
            else:
                target_edge_data = edge_data
        # get all target edges
        target_edges = self.get_edges(
            ids=edge_ids,
            graph_ids=graph_ids,
            types=target_edge_types,
            sources=ids,
            data=target_edge_data,
            query=target_query
        )
        # fill edges
        if target_edges is not None:
            # if target_edges is an edge
            if isinstance(target_edges, Edge):
                # and targets or target_edges is not directed
                if targets or not target_edges.directed:
                    edges.add(target_edges)
            elif targets:  # if targets
                edges |= set(target_edges)
            else:
                for target_edge in target_edges:
                    # add not directed edges
                    if not target_edge.directed:
                        edges.add(target_edge)

        # store edge sources and targets ids before get them at a time
        if not add_edges:
            edge_sources = []
            edge_targets = []

        # add sources and targets from all edges
        for edge in edges:
            if sources or not edge.directed:
                if add_edges:
                    elts = self.get_elts(
                        ids=edge.sources,
                        graph_ids=graph_ids,
                        data=source_data,
                        types=source_types,
                        query=source_query
                    )
                    result[edge] = [
                        GraphElement.new_element(**elt)
                        for elt in elts
                    ]
                else:
                    edge_sources += edge.sources
            if targets or not edge.directed:
                if add_edges:
                    elts = self.get_elts(
                        ids=edge.targets,
                        graph_ids=graph_ids,
                        data=target_data,
                        types=target_types,
                        query=target_query
                    )
                    result[edge] = [
                        GraphElement.new_element(**elt)
                        for elt in elts
                    ]
                else:
                    edge_targets += edge.targets

        # improve complexity if not add_edges
        if not add_edges:
            # get source graph elements
            if edge_sources:
                elts = self.get_elts(
                    ids=edge_sources,
                    graph_ids=graph_ids,
                    data=source_data,
                    types=source_types,
                    query=source_query
                )
                result += [GraphElement.new_element(**elt) for elt in elts]

            # get target graph elements
            if edge_targets:
                elts = self.get_elts(
                    ids=edge_targets,
                    graph_ids=graph_ids,
                    data=target_data,
                    types=target_types,
                    query=target_query
                )
                result += [GraphElement.new_element(**elt) for elt in elts]

        return result

    def get_vertices(
        self,
        ids=None, graph_ids=None, types=None, data=None, query=None
    ):
        """
        Get graph vertices related to some context property.

        :param ids: vertice ids to get.
        :type ids: list or str
        :param graph_ids: vertice graph ids.
        :type graph_ids: list or str
        :param types: vertice type(s).
        :type types: list or str
        :param data: data to find among vertices.
        :param dict query: additional search query.

        :return: list of vertices if ids is a list. One vertice if ids is a
            str.
        :rtype: list or dict
        """

        result = None

        elts = self.get_elts(
            ids=ids,
            graph_ids=graph_ids,
            types=types,
            data=data,
            base_type=Vertice.BASE_TYPE,
            query=query
        )

        if elts is not None:
            if isinstance(elts, dict):
                result = GraphElement.new_element(**elts)
            else:
                result = [GraphElement.new_element(**elt) for elt in elts]

        return result

    def get_edges(
        self,
        ids=None, types=None, sources=None, targets=None, graph_ids=None,
        data=None,
        query=None
    ):
        """
        Get edges related to input ids, types and source/target ids.

        :param ids: edge ids to find. If ids is a str, result is an Edge or
            None.
        :type ids: list or str
        :param types: edge types to find.
        :type types: list or str
        :param sources: source edge attribute to find.
        :type sources: list or str
        :param targets: target edge attribute to find.
        :type targets: list or str
        :param graph_ids: graph ids from where find edges.
        :type graph_ids: list or str
        :param dict query: additional query.

        :return: Edge(s) corresponding to input parameters.
        :rtype: Edge or list of Edges.
        """

        # by default, result is a list
        result = []

        # init unique by default
        unique = False

        if query is None:
            query = {}

        if sources is not None:
            if not isinstance(sources, basestring):
                sources = {'$in': sources}
            query[Edge.SOURCES] = sources

        if targets is not None:
            if not isinstance(targets, basestring):
                targets = {'$in': targets}
            query[Edge.TARGETS] = targets

        edges = self.get_elts(
            ids=ids,
            types=types,
            query=query,
            graph_ids=graph_ids,
            data=data,
            base_type=Edge.BASE_TYPE
        )

        if edges is not None:
            # ensure edges is a list
            if isinstance(edges, dict):
                unique = True
                edges = [edges]
            graph_type = self.GRAPH_TYPE
            for edge in edges:
                elt = graph_type.new_element(**edge)
                if isinstance(elt, Edge):
                    result.append(elt)
        else:
            result = None

        if unique:
            result = result[0] if result else None

        return result
