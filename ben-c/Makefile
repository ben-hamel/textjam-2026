CC      = clang
CFLAGS  = -Wall -Wextra -O2
LDFLAGS = -framework CoreAudio -framework AudioToolbox -framework CoreFoundation -lpthread -lm

TARGET = ben-c

$(TARGET): main.c miniaudio.h
	$(CC) $(CFLAGS) -o $(TARGET) main.c $(LDFLAGS)

clean:
	rm -f $(TARGET)
