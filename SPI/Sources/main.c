#include <hidef.h>      /* common defines and macros */
#include "derivative.h"      /* derivative-specific definitions */

void timer_5_enable(void);
void spi_enable(void);
void pwm_init(void);

char seg_7(char);

uchar seg_7_val = 0;

void main(void) 
{
    /* put your own code here */

    DDRB = 0xFF;
    DDRP |= 0x0F;
    PTP &= 0xF0;
    PTP |= 0x0D;
    PORTB = 0x0F;
    
    spi_enable();

    timer_5_enable();

    EnableInterrupts;


    while(1);
                             
}

void interrupt 13 timer_5_isr(void)
{
    TC5 += 200;
    
    switch(PTP & 0x0F) {
        case 0x07:
            /* First display */
            PTP = 0x0E;
            PORTB = seg_7(seg_7_val / 1000);
            break;
        case 0x0E:
            /* Second display */
            PTP = 0x0D;
            PORTB = seg_7((seg_7_val % 1000) / 100);	
            break;
        case 0x0D:
            /* Third display */
            PTP = 0x0B;
            PORTB = seg_7((seg_7_val % 100) / 10);
            break;
        case 0x0B:
            /* Fourth display */
            PTP = 0x07;
            PORTB = seg_7((seg_7_val % 10));
            break;
    }
    
}

void interrupt 19 spi0_isr(void)
{
    uchar data, spi_reg;
    spi_reg = SPI0SR;
    data = SPI0DR;
    SPI0DR = 0x00;
    seg_7_val = data;    
}

void pwm_init(void) {
      
      PWMCLK = 0;
      PWMPOL = 0xFF;
      PWMPRCLK = 0x22;
      PWMCTL = 0x0C;
      PWMCAE = 0;
      PWMPER0 = 158;
      PWMDTY0 = 79;  
      PWMCNT0 = 0;
      PWME = 0xFF;
      
           
}

void timer_5_enable(void) 
{
    TSCR1 = 0x90;
    TSCR2 = 0x05;
    TIOS = 0x20;
    TCTL1 = 0x0C;
    TFLG1 = 0xFF;
    TC5 = TCNT + 10;
    while(TFLG1 & 0x20);
    TCTL1 = 0x04;
    TIE = 0x20;
}

void spi_enable(void) 
{
    SPI0CR1 |= 0xC0;
    //DDRS = 0x10;
}

char seg_7(char val) 
{
    switch(val) {
        case 0x00:
            return 0x3F;
        case 0x01:
            return 0x06;
        case 0x02:
            return 0x5B;
        case 0x03:
            return 0x4F;
        case 0x04:
            return 0x66;
        case 0x05:
            return 0x6D;
        case 0x06:
            return 0x7D;
        case 0x07:
            return 0x07;
        case 0x08:
            return 0x7F;
        case 0x09:
            return 0x6F;
        case 0x0A:
            return 0x77;
        case 0x0B:
            return 0x7C;
        case 0x0C:
            return 0x39;
        case 0x0D:
            return 0x5E;
        case 0x0E:
            return 0x79;
        case 0x0F:
            return 0x71;
        case 0xFF:
            return 0x00;    /* Turn display off */
    }
}