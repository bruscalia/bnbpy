#include "job.h"
#include <iostream>
#include <cstdlib>

// Empty constructor
Job::Job() : j(0), p(nullptr), lat(nullptr), slope(0), T(0) {}

// Destrutor
Job::~Job() {
    // Free memory
    // if (p != nullptr) {
    //     free(p);
    // }

    // Libera memória de lat
    // if (lat != nullptr) {
    //     for (size_t i = 0; i < r.size(); ++i) {
    //         if (lat[i] != nullptr) {
    //             free(lat[i]);
    //         }
    //     }
    //     free(lat);
    // }
}

// Método para imprimir os atributos de Job
// void Job::printJob() const {
//     std::cout << "Job ID: " << j << "\n";
//     std::cout << "Processing times (p): ";
//     for (size_t i = 0; i < r.size(); ++i) {
//         std::cout << p[i] << " ";
//     }
//     std::cout << "\nRelease times (r): ";
//     for (const auto& value : r) {
//         std::cout << value << " ";
//     }
//     std::cout << "\nDelivery times (q): ";
//     for (const auto& value : q) {
//         std::cout << value << " ";
//     }
//     std::cout << "\nSlope: " << slope << "\n";
//     std::cout << "T: " << T << "\n";
// }
