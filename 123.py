time_lst = ["12:20", "4:30", "9:05"]
for element in time_lst:
    hours, minutes = element.split(":")
    formated = f"{int(hours):{int(minutes)}}"
    print(formated)