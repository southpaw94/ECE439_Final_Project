#include <hidef.h>      /* common defines and macros */
#include "derivative.h"      /* derivative-specific definitions */

void timer_5_enable(void);
void spi_enable(void);
void pwm_init_16();
void pwm_write_0(uchar);
void pwm_write_1(uchar);
void pwm_write_2(uchar);
char seg_7(char);
void MSDelay(char);
uchar seg_7_val = 0;
uchar theta = 1;
 

int buffer[6]= {90,180,0,45,30,60}; //100 byte buffer for values from raspi


void main(void) 
{
    /* put your own code here */                    
    /*unsigned char i; 
    DDRB = 0xFF;
    DDRP = DDRP |  0b00001111;
    PTP &= 0xF0;
    PTP |= 0x0D;
    PORTB = 0x0F; */
    
    pwm_init_16();
    pwm_write_0(90);
    pwm_write_1(90);
    pwm_write_2(0);
    
    spi_enable();

    //timer_5_enable();

    EnableInterrupts;
  
    
    //pwm_write(90, 0, 0);
    while(1)
    {

      
                             
    }
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
    DisableInterrupts;
    
    spi_reg = SPI0SR;
    data = SPI0DR;
    
    switch (theta) 
    {
        case 0:
            pwm_write_0(data);
            break;
        case 1:
            pwm_write_1(data);
            break;
        case 2:
            while (data != 0 && data != 65) 
            {
                while (~PTS_PTS7);   
                data = SPI0DR;     
            }
            pwm_write_2(data);
            break;
    }
    
    if (theta < 2) 
    {
        theta++;
    } else 
    {
        theta = 0;
    }
    
    EnableInterrupts;
}

void pwm_init_16(void) {
  PWMCLK = 0x00;
  PWMPOL = 0x2A;
  PWMPRCLK = 0x44;
  PWMCTL = 0x7C;    //change to 7c to enable cat pwm reg 01, 23 to 45
  PWMCAE = 0x00;
  /* asm {
    movw #30000,PWMPER4
    movw #24000,PWMDTY4
  }  */
  PWMPER0 = 30000 >> 8 & 0xFF;
  PWMPER1 = 30000 & 0xFF;
  PWMPER2 = 30000 >> 8 & 0xFF;
  PWMPER3 = 30000 & 0xFF;
  PWMPER4 = 30000 >> 8 & 0xFF;
  PWMPER5 = 30000 & 0xFF;
  PWMDTY0 = 900 >> 8 & 0xFF;
  PWMDTY1 = 900 & 0xFF;
  PWMDTY2 = 900 >> 8 & 0xFF;
  PWMDTY3 = 900 & 0xFF;
  PWMDTY4 = 900 >> 8 & 0xFF;
  PWMDTY5 = 900 & 0xFF;
  PWME_PWME1 = 1;
  PWME_PWME3 = 1;
  PWME_PWME5 = 1;
}

void pwm_write_0(uchar angle0) 
{
    int dty0 = (int) (900 + (180 - angle0) / 180.0 * 2850.0);
    PWMDTY0 = (dty0 >> 8) & 0xFF;
    PWMDTY1 = dty0 & 0xFF;   
}

void pwm_write_1(uchar angle1) 
{
    int dty1 = (int) (900 + angle1 / 180.0 * 2750.0);
    PWMDTY2 = (dty1 >> 8) & 0xFF;
    PWMDTY3 = dty1 & 0xFF;   
}

void pwm_write_2(uchar angle2) 
{
    int dty2 = (int) (900 + (180 - angle2) / 180.0 * 2850.0);
    PWMDTY4 = (dty2 >> 8) & 0xFF;
    PWMDTY5 = dty2 & 0xFF;   
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
    char dummy_val;
    SPI0CR1 = 0xC0;
    SPI0CR2 = 0x00;
    DDRS = 0x10;
    while (~ SPI0SR & 0x80);
    dummy_val = SPI0DR;
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

void MSDelay(unsigned int itime)  //millisec delay
  {
    unsigned int i; unsigned int j;
    for(i=0;i<itime;i++)
      for(j=0;j<331;j++);
      
  }