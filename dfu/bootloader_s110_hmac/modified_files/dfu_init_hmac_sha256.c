/* Copyright (c) 2014 Nordic Semiconductor. All Rights Reserved.
 *
 * The information contained herein is property of Nordic Semiconductor ASA.
 * Terms and conditions of usage are described in detail in NORDIC
 * SEMICONDUCTOR STANDARD SOFTWARE LICENSE AGREEMENT.
 *
 * Licensees are granted free, non-transferable use of the information. NO
 * WARRANTY of ANY KIND is provided. This heading must NOT be removed from
 * the file.
 *
 */

/**@file
 *
 * @defgroup nrf_dfu_init_template Template file with an DFU init packet handling example.
 * @{
 *
 * @ingroup nrf_dfu
 *
 * @brief This file contains a template on how to implement DFU init packet handling.
 *
 * @details The template shows how device type and revision can be used for a safety check of the 
 *          received image. It shows how validation can be performed in two stages:
 *          - Stage 1: Pre-check of firmware image before transfer to ensure the firmware matches:
 *                     - Device Type.
 *                     - Device Revision.
 *                     Installed SoftDevice.
 *                     This template can be extended with additional checks according to needs.
 *                     For example, such a check could be the origin of the image (trusted source) 
 *                     based on a signature scheme.
 *          - Stage 2: Post-check of the image after image transfer but before installing firmware.
 *                     For example, such a check could be an integrity check in form of hashing or 
 *                     verification of a signature.
 *                     In this template, a simple CRC check is carried out.
 *                     The CRC check can be replaced with other mechanisms, like signing.
 *
 * @note This module does not support security features such as image signing, but the 
 *       implementation allows for such extension.
 *       If the init packet is signed by a trusted source, it must be decrypted before it can be
 *       processed.
 */

#include "dfu_init.h"
#include <stdint.h>
#include <string.h>
#include "bootloader_settings.h"
#include "crc16.h"
#include "dfu_types.h"
#include "nrf_error.h"
#include "nrf_sdm.h"

#include "hmac_sha256.h"

#define UICR_RBPCONF_ADDR                   0x10001004                 /**< Memory location of ReadBack Protection register. This is used to prevent key readback using debugger */

#define SECRET_KEY_ADDR                     0x0003F800                 /**< Memory location of secret key. NOTE: KEY SHOULD NEVER BE MOVED OR UPDATED */
#define SECRET_KEY_SIZE                     32                         /**< Size of secret key. SHA256 = 32 byte key */

#define DFU_INIT_PACKET_EXT_LENGTH_MIN      SECRET_KEY_SIZE            //< Minimum length of the extended init packet. The extended init packet may contain a CRC, a HASH, or other data. This value must be changed according to the requirements of the system. The template uses a minimum value of two in order to hold a CRC. */
#define DFU_INIT_PACKET_EXT_LENGTH_MAX      SECRET_KEY_SIZE            //< Maximum length of the extended init packet. The extended init packet may contain a CRC, a HASH, or other data. This value must be changed according to the requirements of the system. The template uses a maximum value of 10 in order to hold a CRC and any padded data on transport layer without overflow. */

static uint8_t m_extended_packet[DFU_INIT_PACKET_EXT_LENGTH_MAX];      //< Data array for storage of the extended data received. The extended data follows the normal init data of type \ref dfu_init_packet_t. Extended data can be used for a CRC, hash, signature, or other data. */
static uint8_t m_extended_packet_length;                               //< Length of the extended data received with init packet. */

static const uint32_t m_rbpconf_pall_enabled __attribute__((at(UICR_RBPCONF_ADDR))) = 0xFFFF00FF; /* Protect all enabled. */

// Verifying that BOOTLOADER_SETTINGS_ADDRESS is located at the beginning of a flash page
STATIC_ASSERT((BOOTLOADER_SETTINGS_ADDRESS % CODE_PAGE_SIZE) == 0);

void __aeabi_assert(const char * error, const char * file, int line)
{
}

static void nvmc_page_erase(uint32_t address)
{ 
  // Enable erase.
  NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Een;
  while (NRF_NVMC->READY == NVMC_READY_READY_Busy)
  {
  }

  // Erase the page
  NRF_NVMC->ERASEPAGE = address;
  while (NRF_NVMC->READY == NVMC_READY_READY_Busy)
  {
  }
  
  NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Ren;
  while (NRF_NVMC->READY == NVMC_READY_READY_Busy)
  {
  }
}

static void erase_and_reset(uint8_t * p_image, uint32_t image_len)
{
    // If authentication fails:
    // 1) Erase bootloader settings to ensure it does not indicate valid code
    // 2) Erase newly copied firmware image
    // 3) Reset chip
    
    // Disable softdevice to get access to NVMC
    (void) sd_softdevice_disable(); // Ignore return code
    
    // Erase settings page
    nvmc_page_erase(BOOTLOADER_SETTINGS_ADDRESS);
    
    // Erase image pages
    for (int i = 0; i < image_len; i += CODE_PAGE_SIZE)
    {
        nvmc_page_erase((uint32_t) &p_image[i]);
    }
    
    NVIC_SystemReset();
}

uint32_t dfu_init_prevalidate(uint8_t * p_init_data, uint32_t init_data_len)
{
    uint32_t i = 0;
    
    // In order to support signing or encryption then any init packet decryption function / library
    // should be called from here or implemented at this location.

    // Length check to ensure valid data are parsed.
    if (init_data_len < sizeof(dfu_init_packet_t))
    {
        return NRF_ERROR_INVALID_LENGTH;
    }

    // Current template uses clear text data so they can be casted for pre-check.
    dfu_init_packet_t * p_init_packet = (dfu_init_packet_t *)p_init_data;

    m_extended_packet_length = ((uint32_t)p_init_data + init_data_len) -
                               (uint32_t)&p_init_packet->softdevice[p_init_packet->softdevice_len];
    if (m_extended_packet_length < DFU_INIT_PACKET_EXT_LENGTH_MIN)
    {
        return NRF_ERROR_INVALID_LENGTH;
    }

    if (((uint32_t)p_init_data + init_data_len) < 
        (uint32_t)&p_init_packet->softdevice[p_init_packet->softdevice_len])
    {
        return NRF_ERROR_INVALID_LENGTH;
    }

    memcpy(m_extended_packet,
           &p_init_packet->softdevice[p_init_packet->softdevice_len],
           m_extended_packet_length);

/** [DFU init application version] */
    // In order to support application versioning this check should be updated.
    // This template allows for any application to be installed however customer could place a
    // revision number at bottom of application to be verified by bootloader. This could be done at
    // a relative location to this papplication for example Application start address + 0x0100.
/** [DFU init application version] */
    
    // First check to verify the image to be transfered matches the device type.
    // If no Device type is present in DFU_DEVICE_INFO then any image will be accepted.
    if ((DFU_DEVICE_INFO->device_type != DFU_DEVICE_TYPE_EMPTY) &&
        (p_init_packet->device_type != DFU_DEVICE_INFO->device_type))
    {
        return NRF_ERROR_INVALID_DATA;
    }
    
    // Second check to verify the image to be transfered matches the device revision.
    // If no Device revision is present in DFU_DEVICE_INFO then any image will be accepted.
    if ((DFU_DEVICE_INFO->device_rev != DFU_DEVICE_REVISION_EMPTY) &&
        (p_init_packet->device_rev != DFU_DEVICE_INFO->device_rev))
    {
        return NRF_ERROR_INVALID_DATA;
    }

    // Third check: Check the array of supported SoftDevices by this application.
    //              If the installed SoftDevice does not match any SoftDevice in the list then an
    //              error is returned.
    while (i < p_init_packet->softdevice_len)
    {
        if (p_init_packet->softdevice[i] == DFU_SOFTDEVICE_ANY ||
            p_init_packet->softdevice[i++] == SOFTDEVICE_INFORMATION->firmware_id)
        {
            return NRF_SUCCESS;
        }
    }
    
    // No matching SoftDevice found - Return NRF_ERROR_INVALID_DATA.
    return NRF_ERROR_INVALID_DATA;
}


uint32_t dfu_init_postvalidate(uint8_t * p_image, uint32_t image_len)
{
    uint8_t digest[SHA256_DIGEST_LENGTH];
    
    // Calculate HMAC for received image
    if (!HMAC_SHA256_compute(p_image, image_len, (uint8_t*)SECRET_KEY_ADDR, SECRET_KEY_SIZE, digest))
    {
        erase_and_reset(p_image, image_len); // Does not return
        
        return NRF_ERROR_INVALID_DATA; 
    }
    
    // Compare calculated and received HMAC
    if (memcmp(digest, m_extended_packet, sizeof(digest)) == 0)
    {
        return NRF_SUCCESS;
    }
    
    erase_and_reset(p_image, image_len); // Does not return
    
    return NRF_ERROR_INVALID_DATA;
}

