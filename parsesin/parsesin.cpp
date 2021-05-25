/* 
 * This source is released into the public domain.
 * Do with it as you will.
 * It MAY not be fit to suit any purpose.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <mem.h>
#include <math.h>

#define MAX_NUM_PRNS  1024
#define ALL_PRNS      1025
#define JUST_STATS    0

#define NO_START_TIME -1.0
#define NO_END_TIME   999999.0

#define Sign(x)  (double) (x < 0 ? -1: 1)

#define MAX_BUFFER_SIZE 8192

int aiPrnStatsDetrended[MAX_NUM_PRNS];
int aiPrnStatsRaw[MAX_NUM_PRNS];

void Usage( void);
void ParseLog( unsigned char* pucStr_, unsigned long ulRequestedPrn_, FILE* fOut_, bool bDetrended_ );
void ScanForLogs( FILE* fIn_, unsigned long ulPrn_, FILE* fOut_ );
bool CheckCrcOk( unsigned char* pucStr_, int iLength_ );
unsigned long CRC32Value( int iIndex_ );


typedef struct
{
   long   lAdr;
   long   lPower;
} SINB_DATA;

typedef struct
{
   unsigned short usPrn;
   unsigned short usReserved;
   float     fTEC;
   float     fTECRate;
   double    dFirstADR;
   SINB_DATA stSinb[50];
} SINB_CHANNEL_DATA;

typedef struct
{
   unsigned char  ucSOP1;
   unsigned char  ucSOP2;
   unsigned char  ucSOP3;
   unsigned char  ucHeaderLength;
   unsigned short usMessageID;
   unsigned char  ucMessageType;
   unsigned char  ucPortAddress;
   unsigned short usMessageLength;
   unsigned short usSequence;
   unsigned char  ucIdleTime;
   unsigned char  ucTimeStatus;
   unsigned short usWeek;
   unsigned long  ulMilliSecs;
   unsigned long  ulRxStatus;
   unsigned short usReserved;
   unsigned short usSWVersion;
   unsigned long  ulChannels;
} SINB_HEADER_DATA;

void
Usage( void)
{
   fprintf(stderr, "Usage: ParseSin <PRN> <IF>  <OF> <ST> <ET>\r\n");
   fprintf(stderr, "                PRN = 1 to 1024 to output specific PRN\r\n");
   fprintf(stderr, "                PRN = 0 will just output log stats\r\n");
   fprintf(stderr, "                IF  = input path and filename\r\n");
   fprintf(stderr, "                OF  = output path and filename (optional if PRN = 0)\r\n");
   fprintf(stderr, "                ST  = start time (optional)\r\n");
   fprintf(stderr, "                ET  = end time (optional)\r\n");
   exit(1);
}

double
WeekCrossCheck( double dDeltaT_ )
{
   return( fabs(dDeltaT_) > 302400.0 ? dDeltaT_+(-Sign(dDeltaT_))*604800.0:dDeltaT_ );
}

void
ParseLog( unsigned char* pucStr_, unsigned long ulRequestedPrn_, FILE* fOut_, bool bDetrended_ )
{
   unsigned long ulTowMilliSecs;
   static bool   bFirst = true;
   SINB_CHANNEL_DATA stSinbChanData;
   SINB_HEADER_DATA  stSinbHeaderData;

   stSinbHeaderData = *((SINB_HEADER_DATA*) &pucStr_[0]);
   ulTowMilliSecs = stSinbHeaderData.ulMilliSecs;

   for( unsigned long i = 0; i < stSinbHeaderData.ulChannels; i++ )
   {
      stSinbChanData  = *((SINB_CHANNEL_DATA*) &pucStr_[stSinbHeaderData.ucHeaderLength+4 + i*sizeof(SINB_CHANNEL_DATA)]);

      if( bDetrended_ )
      {
         aiPrnStatsDetrended[stSinbChanData.usPrn-1]++;
      }
      else
      {
         aiPrnStatsRaw[stSinbChanData.usPrn-1]++;
      }

      if( (unsigned long) stSinbChanData.usPrn == ulRequestedPrn_ )
      {
         float fTEC;
         float fTECRate;
         double dFirstADR;

         if( bFirst )
         {
            if( NULL != fOut_ )
            {
               if( bDetrended_ )
               {
                  fprintf( fOut_, "Detrended");
               }
               else
               {
                  fprintf( fOut_, "Raw");
               }
               fprintf( fOut_, "   Week Num: %4d   Prn: %2d\n", stSinbHeaderData.usWeek, stSinbChanData.usPrn );
               fprintf( fOut_, "  GPS TOW ,   TEC   ,  TECdot ,  ADR ,   Power   \n" );
            }

            bFirst = false;
         }

         for( int i = 0; i < 50; i++ )
         {
            double dADR;
            double dPower;

            dADR = stSinbChanData.stSinb[i].lAdr/1000.0;

            if( bDetrended_ )
            {
               dPower = stSinbChanData.stSinb[i].lPower/1048576.0;
            }
            else
            {
               dPower = stSinbChanData.stSinb[i].lPower*10000.0;
            }

            if( NULL != fOut_ )
            {
               fprintf( fOut_, "%10.3f,%9.6f,%9.6f,%6.3lf,%11.8lf\n", (double) ulTowMilliSecs/1000.0, stSinbChanData.fTEC,
                                                                      stSinbChanData.fTECRate, stSinbChanData.dFirstADR+dADR, dPower );
            }
            ulTowMilliSecs += 20;
         }

         break;
      }
   }
}

void
ScanForLogs( FILE* fIn_, unsigned long ulPrn_, FILE* fOut_, double dStartTime_, double dEndTime_ )
{
   int i;
   unsigned char aucStr[MAX_BUFFER_SIZE];

   for( i = 0; i < MAX_NUM_PRNS; i++ )
   {
      aiPrnStatsDetrended[i] = 0;
      aiPrnStatsRaw[i] = 0;
   }

   while( !feof(fIn_) )
   {
      aucStr[0] = fgetc( fIn_ );

      if( aucStr[0] == 0xAA )
      {
         aucStr[1] = fgetc( fIn_ );
         if( aucStr[1] == 0x44 )
         {
            aucStr[2] = fgetc( fIn_ );
            if( aucStr[2] == 0x12 )
            {
               aucStr[3] = fgetc( fIn_ );

               unsigned char ucHeaderLength = aucStr[3];

               fread( &aucStr[4], 1, 2, fIn_ );
               unsigned long ulMessageID = (unsigned long)aucStr[4] | ((unsigned long)aucStr[5] << 8);

               aucStr[6] = fgetc( fIn_ ); // Message Type
               aucStr[7] = fgetc( fIn_ ); // Port Address

               fread( &aucStr[8], 1, 2, fIn_ );
               unsigned long ulMessageLength = (unsigned long)aucStr[8] | ((unsigned long)aucStr[9] << 8);

               if( (ulMessageID == 0x146 || ulMessageID == 0x147) && ulMessageLength < MAX_BUFFER_SIZE)
               {
                  bool bDetrended;

                  bDetrended = ulMessageID == 0x146 ? true:false;

                  fread( &aucStr[10], 1, ulMessageLength + ucHeaderLength - 6, fIn_ );

                  if( CheckCrcOk( &aucStr[0], ulMessageLength + ucHeaderLength + 4 ) )
                  {
                     unsigned long ulTowMilliSecs;

                     ulTowMilliSecs = *((unsigned long*) &aucStr[16]);

                     if( dStartTime_ == NO_START_TIME )
                     {
                        dStartTime_ = (double) ulTowMilliSecs/1000.0;
                     }

                     if( WeekCrossCheck( dEndTime_ - (double) ulTowMilliSecs/1000.0 ) < 0 && dEndTime_ != NO_END_TIME )
                     {
                        break;
                     }

                     if( WeekCrossCheck( ((double) ulTowMilliSecs)/1000.0 - dStartTime_ ) >= 0.0 )
                     {
                        ParseLog( &aucStr[0], ulPrn_, fOut_, bDetrended );
                     }
                  }
               }
               else
               {
                  fseek( fIn_, ulMessageLength + ucHeaderLength - 6, SEEK_CUR );
               }
            }
            else
            {
               fseek( fIn_, -2, SEEK_CUR );
            }
         }
         else
         {
            fseek( fIn_, -1, SEEK_CUR );
         }
      }
   }

   fprintf(stdout, "\nPrn #Detrended       #Raw\n");
   for( i = 0; i < MAX_NUM_PRNS; i++ )
   {
      if( aiPrnStatsDetrended[i] > 0 || aiPrnStatsRaw[i] > 0 )
      {
         fprintf(stdout, "%3d %10d %10d\n", i+1, aiPrnStatsDetrended[i], aiPrnStatsRaw[i] );
      }
   }
   fprintf(stdout, "\n");
}

bool
CheckCrcOk( unsigned char* pucStr_, int iLength_ )
{
   unsigned long ulTemp1;
   unsigned long ulTemp2;
   unsigned long ulCRC;
   unsigned long ulStoredCRC;
   unsigned long ulCount;

   ulCount = iLength_ - 4;
   ulStoredCRC = *((unsigned long*)&pucStr_[ulCount]);
   ulCRC = 0;
   while( ulCount-- != 0 )
   {
      ulTemp1 = (ulCRC >> 8) & 0x00FFFFFFL;
      ulTemp2 = CRC32Value( ((int) ulCRC ^ *pucStr_++ ) & 0xFF ); 
      ulCRC = ulTemp1 ^ ulTemp2;
   }

   if( ulCRC == ulStoredCRC )
   {
      return true;
   }
   else
   {
      return false;
   }
}

#define CRC32_POLYNOMIAL  0xEDB88320L

unsigned long
CRC32Value( int iIndex_ )
{
   int j;
   unsigned long ulCRC;

   ulCRC = iIndex_;

   for( j = 8; j > 0; j-- )
   {
      if( ulCRC & 1 )
      {
         ulCRC = (ulCRC >> 1) ^ CRC32_POLYNOMIAL;
      }
      else
      {
        ulCRC >>= 1;
      }
   }

   return ulCRC;
}

int
main( int argc, char* argv[] )
{
   unsigned long ulPrn = 0;
   double dStartTime;
   double dEndTime;
   char*  szInFileName;
   char*  szOutFileName;
   FILE* fIn;
   FILE* fOut;
   
   printf("Line 328");

   if( argc == 3 || argc == 4 || argc == 6 )
   {
      szInFileName  = argv[2];
      szOutFileName = argv[3];

      ulPrn = atol( argv[1] );
      if( (ulPrn < 0) || (ulPrn > MAX_NUM_PRNS) )
      {
         fprintf(stderr, "Invalid PRN number: %lu\r\n", ulPrn );
         Usage();
         exit(1);
      }

      if( argc == 6 )
      {
         dStartTime = atof(argv[4]);
         dEndTime   = atof(argv[5]);
      }
      else
      {
         dStartTime = NO_START_TIME;
         dEndTime   = NO_END_TIME;
      }
   }
   else
   {
      Usage();
   }

   fIn = fopen( szInFileName, "rb");
   if( fIn == NULL )
   {
      fprintf(stderr, "Can't open file: %s\r\n", szInFileName );
      Usage();
      exit(1);
   }

   if( argc > 3 )
   {
      fOut = fopen( szOutFileName, "wb");
      if( fOut == NULL )
      {
         fprintf(stderr, "Can't open file: %s\r\n", szOutFileName );
         Usage();
         exit(1);
      }
   }
   else
   {
      fOut = NULL;
   }

   ScanForLogs( fIn, ulPrn, fOut, dStartTime, dEndTime );

   fclose( fIn );
   fclose( fOut );

   return 0;
}
