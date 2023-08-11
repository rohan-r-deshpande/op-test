#!/usr/bin/env python3
# IBM_PROLOG_BEGIN_TAG
# This is an automatically generated prolog.
#
# $Source: op-test-framework/testcases/MachineConfig.py $
#
# OpenPOWER Automated Test Project
#
# Contributors Listed Below - COPYRIGHT 2023
# [+] International Business Machines Corp.
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#
# IBM_PROLOG_END_TAG


import os
import unittest
import time
import re
import  json

import OpTestConfiguration
import OpTestLogger
from common.OpTestSystem import OpSystemState

log = OpTestLogger.optest_logger_glob.get_logger(__name__)


class MachineConfig(unittest.TestCase):


    def setUp(self):

        conf = OpTestConfiguration.conf
        self.cv_SYSTEM = conf.system()
        self.cv_SYSTEM.goto_state(OpSystemState.OFF)
        self.bmc_type = conf.args.bmc_type
        self.machine_config = json.loads(conf.args.machine_config)
        if self.bmc_type == "FSP_PHYP" or self.bmc_type == "EBMC_PHYP" :
            self.hmc_user = conf.args.hmc_username
            self.hmc_password = conf.args.hmc_password
            self.hmc_ip = conf.args.hmc_ip
            self.lpar_name = conf.args.lpar_name
            self.system_name = conf.args.system_name
            self.cv_HMC = self.cv_SYSTEM.hmc
            self.lpar_prof = conf.args.lpar_prof
        else:
            self.skipTest("Functionality is supported only on LPAR")

    def runTest(self):
        status=0
        if self.machine_config.__contains__('lpar'):
            status=LparConfig(self.cv_HMC,self.system_name,self.lpar_name,self.lpar_prof,self.machine_config['lpar']).LparSetup()
            if status:
                self.fail(status)
        if self.machine_config.__contains__('cec'):
            if not self.cv_HMC.lpar_vios:
                self.skipTest("Please pass lpar_vios in config file.")
            config_value=self.machine_config['cec']
            valid_size = [128, 256, 1024, 2048, 4096]
            if "lmb" in config_value:
                lmb_size = re.findall('lmb=[0-9]+', str(self.machine_config))[0].split('=')[1]
                if int(lmb_size) not in valid_size:
                    self.skipTest("%s is not valid lmb size, "
                                  "valid lmb sizes are 128, 256, 1024, 2048, 4096" % lmb_size)
                status = CecConfig(self.cv_HMC,self.system_name,self.lpar_name,self.lpar_prof,lmb_size).CecSetup_lmb()
                if status:
                    self.fail(status)
            else:
                self.skipTest("Not implemented for other CEC settings")
        else:
            self.skipTest("Not Supported Config")


class LparConfig():

    '''
    pass machine_config in config file indicating proc mode, vtpm and vpmem.
    valid values: cpu=shared or cpu=dedicated
                  vtpm=1 or vtpm=0
                  vpmem=0 or vpmem=1
    Ex: machine_config="cpu=dedicated,vtpm=1,vpmem=1"
    '''
    def __init__(self, cv_HMC=None, system_name= None,
                 lpar_name=None, lpar_prof=None, machin_config =None):
        self.cv_HMC = cv_HMC
        self.system_name = system_name
        self.lpar_name = lpar_name
        self.lpar_prof = lpar_prof
        self.machine_config=machin_config



    def LparSetup(self):
        '''
        If cpu=shared is passed in machine_config lpar proc mode changes to shared mode.
        Pass sharing_mode, min_proc_units, max_proc_units and desired_proc_units in config file.
        Ex:
        sharing_mode=uncap
        min_proc_units=1.0
        max_proc_units=2.0
        desired_proc_units=2.0
        overcommit_ratio=3
        '''

        if "cpu=shared" in self.machine_config:
            conf = OpTestConfiguration.conf
            try: self.sharing_mode = conf.args.sharing_mode
            except AttributeError:
                self.sharing_mode = "cap"
            try: self.min_proc_units = float(conf.args.min_proc_units)
            except AttributeError:
                self.min_proc_units = 1.0
            try: self.desired_proc_units = float(conf.args.desired_proc_units)
            except AttributeError:
                self.desired_proc_units = 2.0
            try: self.max_proc_units = float(conf.args.max_proc_units)
            except AttributeError:
                self.max_proc_units = 2.0
            try: self.overcommit_ratio = int(conf.args.overcommit_ratio)
            except AttributeError:
                self.overcommit_ratio = 1
            proc_mode = 'shared'
            curr_proc_mode = self.cv_HMC.get_proc_mode()
            if proc_mode in curr_proc_mode:
                log.info("System is already booted in shared mode.")
            else:
                self.cv_HMC.profile_bckup()
                self.cv_HMC.change_proc_mode(proc_mode, self.sharing_mode, self.min_proc_units,
                                             self.desired_proc_units, self.max_proc_units, self.overcommit_ratio)

        '''
        If cpu=dedicated is passed in machine_config lpar proc mode changes to dedicated mode.
        Pass sharing_mode, min_proc_units, max_proc_units and desired_proc_units in config file.
        Ex:
        sharing_mode=share_idle_procs
        min_proc_units=1
        max_proc_units=2
        desired_proc_units=2
        '''

        if "cpu=dedicated" in self.machine_config:
            conf = OpTestConfiguration.conf
            try: self.sharing_mode = conf.args.sharing_mode
            except AttributeError:
                self.sharing_mode = "share_idle_procs"
            try: self.min_proc_units = conf.args.min_proc_units
            except AttributeError:
                self.min_proc_units = "1"
            try: self.desired_proc_units = conf.args.desired_proc_units
            except AttributeError:
                self.desired_proc_units = "2"
            try: self.max_proc_units = conf.args.max_proc_units
            except AttributeError:
                self.max_proc_units = "2"
            proc_mode = 'ded'
            curr_proc_mode = self.cv_HMC.get_proc_mode()
            if proc_mode in curr_proc_mode:
                log.info("System is already booted in dedicated mode.")
            else:
                self.cv_HMC.profile_bckup()
                self.cv_HMC.change_proc_mode(proc_mode, self.sharing_mode, self.min_proc_units,
                                             self.desired_proc_units, self.max_proc_units)


        if "vtpm=1" in self.machine_config:
            vtpm_enabled = self.cv_HMC.vtpm_state()
            if vtpm_enabled[0] == "1":
                log.info("System is already booted with VTPM enabled")
            else:
                proc_compat_mode = self.cv_HMC.get_proc_compat_mode()
                if "POWER10" in proc_compat_mode:
                    self.vtpm_version = 2.0
                    try: self.vtpm_encryption = conf.args.vtpm_encryption
                    except AttributeError:
                        self.vtpm_encryption = "Power10v1"
                elif proc_compat_mode[0] in ["POWER9_base", "POWER9", "POWER8"]:
                    self.vtpm_version = 1.2
                else:
                    log.info("Unknown processor compact mode")
                self.cv_HMC.enable_vtpm(self.vtpm_version, self.vtpm_encryption)
                vtpm_enabled = self.cv_HMC.vtpm_state()
                if vtpm_enabled[0] == "1":
                    log.info("System booted with VTPM enabled")
                else:
                    return "Failed to boot with vtpm enabled"

        elif "vtpm=0" in self.machine_config:
            vtpm_enabled = self.cv_HMC.vtpm_state()
            if vtpm_enabled[0] == "0":
                log.info("System is already booted with VTPM disabled")
            else:
                self.vtpm_mode = '0'
                self.cv_HMC.disable_vtpm()
                vtpm_enabled = self.cv_HMC.vtpm_state()
                if vtpm_enabled[0] == "0":
                    log.info("System booted with VTPM disabled")
                else:
                    return "Failed to boot with vtpm disabled"


        if "vpmem=1" in self.machine_config:
            try: self.pmem_name = conf.args.pmem_name
            except AttributeError:
                self.pmem_name = "vol1"
            try: self.pmem_size = conf.args.pmem_size
            except AttributeError:
                self.pmem_size = "8192"
            if self.cv_HMC.vpmem_count() [0] >= "1":
                self.cv_HMC.remove_vpmem()
            current_lmb = self.cv_HMC.get_lmb_size()
            if int(self.pmem_size) % int(current_lmb[0]) != 0:
                self.fail("pmem_size should be multiple of %s" % current_lmb)
            self.cv_HMC.configure_vpmem(self.pmem_name, self.pmem_size)
            curr_num_volumes = self.cv_HMC.vpmem_count()
            if curr_num_volumes[0] >= "1":
                log.info("Configured vpmem %s of %sMB" % (self.pmem_name, self.pmem_size))
            else:
                return "Failed to configure pmem"

        if "nx_gzip" in self.machine_config:
            conf = OpTestConfiguration.conf
            try: self.qos_credits =  round(float(conf.args.qos_credits))
            except AttributeError:
                self.qos_credits = 10
            proc_compat_mode = self.cv_HMC.get_proc_compat_mode()
            if "POWER10" in proc_compat_mode:
                self.cv_HMC.configure_gzip_qos(self.qos_credits)
            else:
                log.info("nx_gzip is supported only in Power10 mode")   


        self.cv_HMC.run_command("chsysstate -r lpar -m %s -o on -n %s -f %s" %
                               (self.system_name, self.lpar_name, self.lpar_prof))
        time.sleep(5)
        curr_proc_mode = self.cv_HMC.get_proc_mode()
        if proc_mode in curr_proc_mode:
            log.info("System booted with %s mode" % proc_mode)
        else:
            return "Failed to boot in %s mode" % proc_mode


class RestoreLAPRConfig(MachineConfig):

    '''
    This class boots the lpar with previous profile, this can be called after ChangeToSharedMode or ChangeToDedicatedMode.
    '''

    def setUp(self):
        super(RestoreLAPRConfig, self).setUp()
        conf = OpTestConfiguration.conf

    def runTest(self):
        self.cv_HMC.poweroff_lpar()
        self.cv_HMC.lpar_prof = self.cv_HMC.lpar_prof + "_bck"
        self.cv_HMC.poweron_lpar()


class CecConfig():

    '''
    This class configures LMB. Pass lmb_size to machine_config in config file.
    Ex: machine_config="lmb=4096, hugepage=16GB"
    Valid LMB values are "128,256,1024,2048,4096"
    '''
    def __init__(self, cv_HMC=None, system_name= None,
                 lpar_name=None, lpar_prof=None, lmb=None):

        self.cv_HMC = cv_HMC
        self.system_name = system_name
        self.lpar_name = lpar_name
        self.lpar_prof = lpar_prof
        self.lmb_size = lmb

    def CecSetup_lmb(self):
        current_lmb = self.cv_HMC.get_lmb_size()
        if int(current_lmb[0]) == int(self.lmb_size):
            log.info("System is already booted with LMB %s" % self.lmb_size)
        else:
            self.cv_HMC.configure_lmb(self.lmb_size)
            self.cv_HMC.poweroff_system()
            self.cv_HMC.poweron_system()
            current_lmb = self.cv_HMC.get_lmb_size()
            if int(current_lmb[0]) == int(self.lmb_size):
                log.info("System booted with LMB %s" % self.lmb_size)
            else:
                return "Failed to boot with LMB %s" % self.lmb_size
            self.cv_HMC.run_command("chsysstate -r lpar -m %s -o on -n %s -f %s" %
                                   (self.system_name, self.lpar_name, self.lpar_prof))
            time.sleep(5)