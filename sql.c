#include <stdio.h>
#include <stdlib.h>
#include <bcm2835.h>
#include <unistd.h>
#include <string.h>
#include <my_global.h>
#include <mysql.h>

void finish_with_error(MYSQL *con)
{
	fprintf(stderr, "%s\n", mysql_error(con));
	mysql_close(con);
	exit(1);
}


int main(int argc, char **argv)
{
	int i;
	long delay;
	unsigned long iter = 0;
    if (!bcm2835_init())
    {
      printf("bcm2835_init failed. Are you running as root??\n");
      return 1;
    }

    if (!bcm2835_spi_begin())
    {
      printf("bcm2835_spi_begin failed. Are you running as root??\n");
      return 1;
    }
    bcm2835_spi_setBitOrder(BCM2835_SPI_BIT_ORDER_MSBFIRST);      // The default
    bcm2835_spi_setDataMode(BCM2835_SPI_MODE0);                   // The default
    bcm2835_spi_setClockDivider(BCM2835_SPI_CLOCK_DIVIDER_16384); // The default
    bcm2835_spi_chipSelect(BCM2835_SPI_CS0);                      // The default
    bcm2835_spi_setChipSelectPolarity(BCM2835_SPI_CS0, LOW);      // the default

	printf("Press Enter to continue\n");
	getchar();

	/* initialized the SQL connection */
	MYSQL *con = mysql_init(NULL);

	if (con == NULL) {
		fprintf(stderr, "mysql_init() failed\n");
		exit(1);
	}

	if (mysql_real_connect(con, "localhost", "root", "passwd", "ECE_439", 0, NULL, 0) == NULL) {
		finish_with_error(con);
	}

	if (mysql_query(con, "SELECT * FROM ANGLES")) {
		finish_with_error(con);
	}

	MYSQL_RES *result = mysql_store_result(con);

	if (result == NULL) {
		finish_with_error(con);
	}

	int num_fields = mysql_num_fields(result);

	MYSQL_ROW row;

	while ((row = mysql_fetch_row(result))) {
		iter++;
		if (iter < 5) {
			delay = 50000;
		} else {
			delay = 50000;
		}
		printf("Sending packet %i\n", iter);
		for (i = 1; i < num_fields; i++) {
			unsigned char send_data = (unsigned char) atoi(row[i]);
   			uint8_t read_data = bcm2835_spi_transfer((unsigned char) send_data);
   			printf("Sent to SPI: %u\n", send_data);
			usleep(10000);
			/* printf("%s ", row[i]); */
		}
		usleep(delay);
		printf("\n");
	}

	mysql_free_result(result);
	mysql_close(con);

	exit(0);

}
