#coding=utf-8
import time

from .command_line import commandLine

from .create_dirctory import createpackageListDir

from .device_info import adbstatus, model

from .save_files import saveAdbLog
from .save_files import saveMemInfoBeforeTest
from .save_files import saveMemInfo
from .save_files import saveMemInfoAfterClearProcess
from .device_info import deviceScreenWidth
from .device_info import deviceScreenHeight


def getAppPackageName(create_time, device_id):
    install_view_apk_cmd = 'adb -s '+device_id+' install -r package_name_viewer.apk'
    commandLine(install_view_apk_cmd).wait(10)

    launch_view_apk_cmd = 'adb -s '+device_id+' shell am start -n com.gionee.packages/com.gionee.packages.MainActivity'
    commandLine(launch_view_apk_cmd).wait(10)

    save_list_to_pc_cmd = 'adb -s '+device_id+' pull /sdcard/packages_visual.txt ' + \
                          createpackageListDir(create_time, device_id)+'packages_names_list.txt'
    commandLine(save_list_to_pc_cmd).wait(10)

    uninstall_view_apk_cmd = 'adb -s '+device_id+' uninstall com.gionee.packages'
    commandLine(uninstall_view_apk_cmd).wait(10)

    remove_list_in_phone_cmd = 'adb -s '+device_id+' shell rm /sdcard/packages_visual.txt'
    commandLine(remove_list_in_phone_cmd).wait(10)

    print(time.ctime()+"~~ Device "+device_id+":Get app's package names success.")

    # getPackageNames_cmd = 'adb -s ' + device_id + ' shell pm list packages > ' \
    #                       + createpackageListDir(create_time, device_id)+'packages_names_list.txt'
    # commandLine(getPackageNames_cmd).wait(10)

    openapplists = open(createpackageListDir(create_time, device_id)+'packages_names_list.txt', 'r')
    applists = openapplists.readlines()
    openapplists.close()

    print(time.ctime()+"~~ Device "+device_id+':App lists load successfully, total '+str(len(applists))+' apps.')
    
    test_packages = ''
    
    for line in applists:
        if line == '\n':
            pass
        else:
            line = line.strip('\n')
            # line = line.replace('package:', '')
            test_packages += '-p '+line+' '
    return test_packages


def killMonkeyTestProcess(device_id):
    view_monkey_test_process_cmd = 'adb -s '+device_id+' shell "ps | grep monkey"'
    monkey_test_process = commandLine(view_monkey_test_process_cmd).stdout.read()
    monkey_test_process = monkey_test_process.decode()
    monkey_test_process = monkey_test_process.split(' ')[5]
    
    kill_monkey_test_process_cmd = 'adb -s '+device_id+' shell kill '+str(monkey_test_process)

    try:
        print(time.ctime() + "~~ Device " + device_id + ':Killing monkey test process.')
        commandLine(kill_monkey_test_process_cmd).wait(10)
        print(time.ctime() + "~~ Device " + device_id + ':Monkey test process killed.')

    except:
        print(time.ctime() + "~~ Device " + device_id + ":Did not found monkey test process.")


def killBackgroundProcess(is_cleaning_background_progress, device_id):
    screenWidth = deviceScreenWidth(device_id)
    screenHeight = deviceScreenHeight(device_id)

    if model(device_id) == 'W909':
        kill_all_background_apps_cmd = 'adb -s ' + device_id \
                                       + ' shell input keyevent KEYCODE_APP_SWITCH; input tap 360 1115'
    else:
        kill_all_background_apps_cmd = 'adb -s ' + device_id \
                                       + ' shell input keyevent KEYCODE_APP_SWITCH; input tap ' \
                                       + str(int(540 / 1080 * screenWidth)) + ' ' + str(int(1580 / 1920 * screenHeight))

    if is_cleaning_background_progress == 'yes':
        print(time.ctime() + "~~ Device " + device_id + ':Killing background processes.')
        commandLine(kill_all_background_apps_cmd).wait(30)


#Definition for result save
def monkeytest(create_time, device_id, test_package_names, running_time, catch_log_interval,
               is_cleaning_background_progress):
    print(time.ctime()+"~~ Device "+device_id+':Rebooting, please wait.')
    device_reboot_cmd = 'adb -s '+device_id+' reboot'
    commandLine(device_reboot_cmd).wait(10)

    adb_wait_for_device_cmd = 'adb -s ' + device_id + ' wait-for-device'
    try:
        commandLine(adb_wait_for_device_cmd).wait(90)
    except:
        print(time.ctime()+"~~ Device "+device_id+':Connection timeout after 90s, test will not execute.')

    print(time.ctime()+"~~ Device "+device_id+':Wait 30s for device stable.')
    time.sleep(30)
    
    count = int(running_time*60*60*1000/500)
    
    if adbstatus(device_id) == "device":

        save_memory_info_before_test = 'adb -s ' + device_id + ' shell dumpsys meminfo > ' + \
                                       saveMemInfoBeforeTest(create_time, device_id)
        monkey_cmd = 'adb -s '+device_id+' shell monkey '+test_package_names + \
                     '--throttle 500 --ignore-crashes --ignore-security-exceptions ' \
                     '--ignore-timeouts --monitor-native-crashes -v -v ' + \
                     str(count)+' > '+saveAdbLog(create_time, device_id)

        print(time.ctime()+"~~ Device "+device_id+':Connection successful, wait for 5 minutes before test')
        time.sleep(300)
        
        print(time.ctime()+"~~ Device "+device_id+':Catching memory info before test.')
        commandLine(save_memory_info_before_test).wait(30)
    
        print(time.ctime()+"~~ Device "+device_id+':Starting monkey test.')
        commandLine(monkey_cmd)
    
        running_count = int(running_time/catch_log_interval)
        
        for i in range(running_count-1):
            time.sleep(catch_log_interval*60)
            killMonkeyTestProcess(device_id)

            print(time.ctime()+"~~ Device "+device_id+':Catching memory info.')
            save_memory_info_cmd = 'adb -s ' + device_id + ' shell dumpsys meminfo > ' + \
                                   saveMemInfo(create_time, device_id)
            commandLine(save_memory_info_cmd).wait(30)

            killBackgroundProcess(is_cleaning_background_progress, device_id)

            print(time.ctime()+"~~ Device "+device_id+':Catching memory info after clear processes.')
            save_memory_info_after_clear_process_cmd = 'adb -s ' + device_id + ' shell dumpsys meminfo > ' + \
                                                       saveMemInfoAfterClearProcess(create_time, device_id)
            commandLine(save_memory_info_after_clear_process_cmd).wait(30)
    
            print(time.ctime()+"~~ Device "+device_id+':Starting monkey test.')
            # monkey_cmd = 'adb -s '+device_id+' shell monkey '+test_package_names + \
            #              '--throttle 500 --ignore-crashes --ignore-security-exceptions ' \
            #              '--ignore-timeouts --monitor-native-crashes -v -v '\
            #              + str(count)+' > '+saveAdbLog(create_time, device_id)
            commandLine(monkey_cmd)
        
        time.sleep(catch_log_interval*60)
        killMonkeyTestProcess(device_id)

        print(time.ctime()+"~~ Device "+device_id+':Catching memory info.')
        save_memory_info_cmd = 'adb -s ' + device_id + ' shell dumpsys meminfo > ' + \
                               saveMemInfo(create_time, device_id)
        commandLine(save_memory_info_cmd).wait(30)

        killBackgroundProcess(is_cleaning_background_progress, device_id)
        
        print(time.ctime()+"~~ Device "+device_id+':Catching memory info after clear processes.')
        save_memory_info_after_clear_process_cmd = 'adb -s ' + device_id + ' shell dumpsys meminfo > ' + \
                                                   saveMemInfoAfterClearProcess(create_time, device_id)
        commandLine(save_memory_info_after_clear_process_cmd).wait(30)
        
    else:
        print(time.ctime()+"~~ Device "+device_id+':Connection failed, please check and fix this.')

    print(time.ctime()+"~~ Device "+device_id+':Test finished.')
