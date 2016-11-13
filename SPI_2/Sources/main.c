#include <hidef.h>      /* common defines and macros */
#include "derivative.h"      /* derivative-specific definitions */

void timer_5_enable(void);
void spi_enable(void);
void pwm_init(void);
void pwm_write(unsigned char,unsigned char,unsigned char); 
char seg_7(char);
void MSDelay(char);
uchar seg_7_val = 0;
 

int buffer[6]= {90,180,0,45,30,60}; //100 byte buffer for values from raspi


void main(void) 
{
    /* put your own code here */                    
    char i; 
    DDRB = 0xFF;
    DDRP = DDRP |  0b00001111;
    PTP &= 0xF0;
    PTP |= 0x0D;
    PORTB = 0x0F;
    
    // spi_enable();

    // timer_5_enable();

    // EnableInterrupts;
    pwm_init();
    PWMDTY4 = (char) ( 37.0 + (180.0 / 180.0)* 113.0);
    pwm_write(0,0,0); 
    MSDelay(1000);
    pwm_write(90, 0, 0);
    while(1)
    {
      /* for (i = 0; i < 6; i++)
       {   
         pwm_write( buffer[i],0,0);
         MSDelay(30); 
         PORTB = seg_7(buffer[i]);
        } 
         */
                             
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
    spi_reg = SPI0SR;
    data = SPI0DR;
    SPI0DR = 0x00;
    seg_7_val = data;    
}

void pwm_init(void) 
{
 
        
  PWMPRCLK=0x05; //ClockA=Fbus/2**8=250KHz
	PWMSCLA=0x01; 	 //ClockSA=12MHz/2x125=48KHz
	PWMCLK=0x10; 	 //ClockSA for chan 4
	PWMPOL=0x10; 		     //high then low for polarity
	PWMCAE=0x0; 		     //left aligned
	PWMCTL=0x0;	         //8-bit chan, PWM during freeze and wait
	PWMPER4=208;
 	 //PWM_Freq=ClockSA/100=6000Hz/100=60Hz. CHANGE THIS
	PWMDTY4=150; 	 //50% duty cycle           AND THIS TO SEE THE EFFECT ON MOTOR. TRY LESS THAN 10%
	PWMCNT4=10;		 //clear initial counter. This is optional
	PWME=0x10; 	   //Enable chan 4 PWM
           
}

void pwm_write(unsigned char theta_1, char theta_2,char theta_3) 
{
  char angle1,angle2,angle3;

  angle1 = (char) ( 37.0 + (theta_1 / 180.0)* 113.0);
  PWMDTY4 = angle1; 
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

void MSDelay(unsigned int itime)  //millisec delay
  {
    unsigned int i; unsigned int j;
    for(i=0;i<itime;i++)
      for(j=0;j<331;j++);
      
  }