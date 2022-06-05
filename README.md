# fp-progjar

[Membuat HTTP Server dan Klien]
Ketentuannya adalah mengimplementasikan RFC 2616 (dituliskan dengan subbab) sebagai berikut
- Mempuat aplikasi HTTP klien dan server
- HTTP klien hanya bertugas untuk request dan melakukan parsing html pada response dari server 
- Method yang diimplementasikan: GET, HEAD, POST (9.3, 9.4, 9.5)
- Status code: 200, 301, 403, 404, 500 (10.2.1, 10.3.2, 10.4.4, 10.4.5, 10.5.1)
- Menerapkan teknik multiclient dengan modul select DAN thread