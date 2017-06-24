from Sun import Sun

coords = {'longitude' : 105.27, 'latitude' : 40.01 }

sun = Sun()

print sun.getCurrentUTC( )

# Sunrise time UTC (decimal, 24 hour format)
print sun.getSunriseTime( coords )

# Sunset time UTC (decimal, 24 hour format)
print sun.getSunsetTime( coords )