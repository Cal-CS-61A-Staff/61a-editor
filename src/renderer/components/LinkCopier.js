import React from "react";
import "../style/FileNameField.css";

export default function LinkCopier({ link, children }) {
    const handleClick = () => {
        navigator.clipboard.writeText(link);
    };

    return (
        <>
            <p>
                {children}
            </p>
            <input className="fileNameField" readOnly value={link} />
            <button className="fileNameSubmitBtn" type="button" onClick={handleClick}> Copy </button>
            <p />
        </>
    );
}
