#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import os
import stat
import struct
import sys
import unittest
import urllib2

import rosinstall.config
from rosinstall.config import MultiProjectException

class MockVcsClient():

    def __init__(self,
                 path_exists = False,
                 checkout_success = True,
                 update_success = True,
                 vcs_presence = True,
                 url = "mockurl"):
        self.path_exists_flag = path_exists
        self.checkout_success = checkout_success
        self.update_success = update_success
        self.vcs_presence = vcs_presence
        self.mockurl = url
        self.checkedout = vcs_presence
        self.updated = False
        
    def get_vcs_type_name(self):
        return "mocktype"

    def get_diff(self, basepath=None):
        return "mockdiff%s"%basepath

    def get_version(self, revision=None):
        return "mockversion%s"%revision
  
    def get_status(self, basepath=None, untracked=False):
        return "mockstatus%s,%s"%(basepath, untracked)

    def path_exists(self):
        return self.path_exists_flag

    def checkout(self, uri=None, version=None):
        self.checkedout = True
        return self.checkout_success

    def update(self, version):
        self.updated = True
        return self.update_success

    def detect_presence(self):
        return self.vcs_presence

    def get_url(self):
        return self.mockurl
    
class testYamlIO(unittest.TestCase):

    def test_get_yaml_from_uri_from_file(self):
        file = os.path.join("test", "example.yaml")
        y = rosinstall.config.get_yaml_from_uri(file)
        
        self.assertTrue("text" in y)
        self.assertTrue(y["text"] == "foobar")

        self.assertTrue("number" in y)
        self.assertTrue(y["number"] == 2)
        # invalid
        try:
            yaml = rosinstall.config.get_yaml_from_uri(os.path.join("test", "example-broken.yaml"))
        except MultiProjectException:
            pass

        
    def test_get_yaml_from_uri_from_missing_file(self):
        file = "/asdfasdfasdfasfasdf_does_not_exist"
        try:
            rosinstall.config.get_yaml_from_uri(file)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

#TODO Fix this
#    def test_get_yaml_from_uri_from_non_yaml_file(self):
#        file = os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "Makefile")
#        y = rosinstall.config.get_yaml_from_uri(file)
#        self.assertEqual(y, None)

    def test_simple_config_element_API(self):
        path = "some/path"
        localname = "some/local/name"
        other1 = rosinstall.config.ConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertFalse(other1.is_vcs_element())
        other1 = rosinstall.config.OtherConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual([{'other': {'local-name': 'some/path'}}], other1.get_yaml())
        self.assertFalse(other1.is_vcs_element())
        other1 = rosinstall.config.SetupConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual([{'setup-file': {'local-name': 'some/path'}}], other1.get_yaml())
        self.assertFalse(other1.is_vcs_element())

    def test_mock_vcs_config_element_init(self):
        path = "some/path"
        localname = "some/local/name"
        try:
            rosinstall.config.VCSConfigElement(None, None, None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            rosinstall.config.VCSConfigElement("path", None, None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            rosinstall.config.VCSConfigElement(None, MockVcsClient(), None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            rosinstall.config.VCSConfigElement("path", MockVcsClient(), None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            rosinstall.config.VCSConfigElement("path", None, None, "some/uri")
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            rosinstall.config.VCSConfigElement(None, MockVcsClient(), None, "some/uri")
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        path = "some/path"
        localname = "some/local/name"
        uri = 'some/uri'
        version='some.version'
        vcsc = rosinstall.config.VCSConfigElement(path, MockVcsClient(), localname, uri)
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mockdiffNone", vcsc.get_diff())
        self.assertEqual("mockstatusNone,False", vcsc.get_status())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'uri': 'some/uri'}}], vcsc.get_yaml())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'version': 'mockversionNone', 'uri': 'some/uri', 'revision': ''}}], vcsc.get_versioned_yaml())
        
        vcsc = rosinstall.config.VCSConfigElement(path, MockVcsClient(), localname, uri, None)
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mockdiffNone", vcsc.get_diff())
        self.assertEqual("mockstatusNone,False", vcsc.get_status())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'uri': 'some/uri'}}], vcsc.get_yaml())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'version': 'mockversionNone', 'uri': 'some/uri', 'revision': ''}}], vcsc.get_versioned_yaml())

        vcsc = rosinstall.config.VCSConfigElement(path, MockVcsClient(), localname, uri, version)
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mockdiffNone", vcsc.get_diff())
        self.assertEqual("mockstatusNone,False", vcsc.get_status())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'version': 'some.version', 'uri': 'some/uri'}}], vcsc.get_yaml())
        self.assertEqual([{'mocktype': {'local-name': 'some/path', 'version': 'mockversionNone', 'uri': 'some/uri', 'revision': 'mockversionsome.version'}}], vcsc.get_versioned_yaml())

    def test_mock_install(self):
        path = "some/path"
        localname = "some/local/name"
        uri = 'some/uri'
        version='some.version'
        mockclient = MockVcsClient(url = uri)
        vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
        vcsc.install()
        self.assertTrue(mockclient.checkedout)
        self.assertFalse(mockclient.updated)
        # checkout failure
        mockclient = MockVcsClient(url = uri, checkout_success = False )
        try:
            vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
            vcsc.install()
            self.fail("should have raised Exception")
        except MultiProjectException: pass
        # path exists no vcs, robust
        mockclient = MockVcsClient(url = uri, path_exists = True, vcs_presence = False )
        try:
            vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
            vcsc.install(robust = True)
            self.fail("should have raised Exception")
        except MultiProjectException: pass
        # uri mismatch, robust
        mockclient = MockVcsClient(url = uri + "invalid", path_exists = True)
        try:
            vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
            vcsc.install(robust = True)
            self.fail("should have raised Exception")
        except MultiProjectException: pass
        # update failure
        mockclient = MockVcsClient(url = uri, path_exists = True, update_success = False )
        try:
            vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
            vcsc.install()
            self.fail("should have raised Exception")
        except MultiProjectException: pass
        # path exists no vcs failure skip
        mockclient = MockVcsClient(url = uri, path_exists = True, vcs_presence = False )
        vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
        vcsc.install(arg_mode='skip')
        # uri mismatch skip
        mockclient = MockVcsClient(url = uri + "invalid", path_exists = True)
        vcsc = rosinstall.config.VCSConfigElement(path, mockclient, localname, uri, None)
        vcsc.install(arg_mode='skip')