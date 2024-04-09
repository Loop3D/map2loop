# import pkg_resources
import site
import os

def load_clut(state):
    stream = './map2loop/_datasets/clut_files/{}_clut.csv'.format(state)
    return stream

def get_install_path():
    site_packages = site.getsitepackages()
    for site_package in site_packages:
        package_path = os.path.join(site_package, 'map2loop')
    return package_path

def load_config(state):
    stream = os.path.join(get_install_path(), 'map2loop\\_datasets\\config_files\\{}_config.json'.format(state))
    return stream
######## this works if map2loop is NOT installed in editable mode




class AustraliaStateUrls:
    aus_geology_urls = {
        "WA": "http://13.211.217.129:8080/geoserver/loop/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=loop:500k_geol_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "QLD": "http://13.211.217.129:8080/geoserver/QLD/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=QLD:qld_geol_asud&bbox={BBOX_STR}&srsName=EPSG:28355&outputFormat=shape-zip",
        "SA": "http://13.211.217.129:8080/geoserver/SA/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=SA:2m_surface_geology_28354_relage&bbox={BBOX_STR}&srs=EPSG:28354&outputFormat=shape-zip",
        "VIC": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=VIC:geolunit_250k_py_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NSW": "http://13.211.217.129:8080/geoserver/NSW/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=NSW:ge_rockunit_lao2&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "ACT": "",
        "TAS": "http://13.211.217.129:8080/geoserver/TAS/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=TAS:geol_poly_250_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NT": "",
    }
    aus_structure_urls = {
        "WA": "http://13.211.217.129:8080/geoserver/loop/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=loop:waroxi_wa_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "QLD": "http://13.211.217.129:8080/geoserver/QLD/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=QLD:outcrops_28355&bbox={BBOX_STR}&srsName=EPSG:28355&outputFormat=shape-zip",
        "SA": "http://13.211.217.129:8080/geoserver/SA/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=SA:sth_flinders_28354&bbox={BBOX_STR}&srs=EPSG:28354&outputFormat=shape-zip",
        "VIC": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=VIC:struc_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NSW": "http://13.211.217.129:8080/geoserver/NSW/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=NSW:lao_struct_pt&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "ACT": "",
        "TAS": "http://13.211.217.129:8080/geoserver/TAS/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=TAS:geol_struc_250_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NT": "",
    }
    aus_fault_urls = {
        "WA": "http://13.211.217.129:8080/geoserver/loop/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=loop:500k_faults_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "QLD": "http://13.211.217.129:8080/geoserver/QLD/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=QLD:qld_faults_folds_28355&bbox={BBOX_STR}&srsName=EPSG:28355&outputFormat=shape-zip",
        "SA": "http://13.211.217.129:8080/geoserver/SA/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=SA:2m_linear_structures&bbox={BBOX_STR}&srs=EPSG:28354&outputFormat=shape-zip",
        "VIC": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=VIC:geolstructure_250k_ln_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NSW": "http://13.211.217.129:8080/geoserver/NSW/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=NSW:faults_joined_left_contains_drop_dups&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "ACT": "",
        "TAS": "http://13.211.217.129:8080/geoserver/TAS/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=TAS:geol_line_250_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NT": "",
    }
    aus_fold_urls = {
        "WA": "http://13.211.217.129:8080/geoserver/loop/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=loop:500k_faults_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "QLD": "http://13.211.217.129:8080/geoserver/QLD/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=QLD:qld_faults_folds_28355&bbox={BBOX_STR}&srsName=EPSG:28355&outputFormat=shape-zip",
        "SA": "http://13.211.217.129:8080/geoserver/SA/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=SA:2m_linear_structures&bbox={BBOX_STR}&srs=EPSG:28354&outputFormat=shape-zip",
        "VIC": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=VIC:geolstructure_250k_ln_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NSW": "http://13.211.217.129:8080/geoserver/NSW/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=NSW:folds_lao&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "ACT": "",
        "TAS": "http://13.211.217.129:8080/geoserver/TAS/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=TAS:geol_line_250_28355&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "NT": "",
    }
    aus_mindep_loopdata = {
        "WA": "http://13.211.217.129:8080/geoserver/loop/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=loop:mindeps_2018_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "QLD": "http://13.211.217.129:8080/geoserver/QLD/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=qld_mindeps_28355&bbox={BBOX_STR}&srsName=EPSG:28355&outputFormat=shape-zip",
        "SA": "",
        "VIC": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=VIC:mindeps_2018_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "NSW": "http://13.211.217.129:8080/geoserver/NSW/wfs?service=WFS&version=1.1.0&request=GetFeature&typeName=NSW:nsw_mindeps&bbox={BBOX_STR}&srs=EPSG:28355&outputFormat=shape-zip",
        "ACT": "",
        "TAS": "http://13.211.217.129:8080/geoserver/VIC/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=VIC:mindeps_2018_28350&bbox={BBOX_STR}&srs=EPSG:28350&outputFormat=shape-zip",
        "NT": "",
    }
    aus_config_urls = {
        "WA": load_config('WA'),
        "QLD": load_config('QLD'),
        "SA": load_config('SA'),
        "VIC": load_config('VIC'),
        "NSW": load_config('NSW'),
        "ACT": "",
        "TAS": load_config('TAS'),
        "NT": "",
    }
    aus_clut_urls = {
        "WA": load_clut('WA'),
        "QLD": load_clut('QLD'),
        "SA": load_clut('SA'),
        "VIC": "",
        "NSW": "",
        "ACT": "",
        "TAS": "",
        "NT": "",
    }
