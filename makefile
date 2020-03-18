CC = gcc
CCFLAGS = -std=gnu99
SRCS = ftserver.c
OBJS = $(SRCS:.c=.o)
EXEC = ftserver

$(EXEC): $(OBJS)
	$(CC) $(OBJS) -o $(EXEC)

%.o: %.c
	$(CC) $(CCFLAGS) -c $<

clean:
	$(RM) $(EXEC) $(OBJS)

