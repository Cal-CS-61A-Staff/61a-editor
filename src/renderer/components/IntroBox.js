import React from "react";
import IntroButton from "./IntroButton";

export default function IntroBox(props) {
    return (
        <div className="introHolder">
            <div className="introTitle">61A Code</div>
            <IntroButton name="Create new file" onClick={() => props.onCreateClick()} />
            <IntroButton name="Open existing file" onClick={props.onOpenClick} />
            <IntroButton name="Start Python interpreter" onClick={() => props.onCreateClick(".py")} />
            <IntroButton name="Start Scheme interpreter" onClick={() => props.onCreateClick(".scm")} />
            <IntroButton name="Start SQL interpreter" onClick={() => props.onCreateClick(".sql")} />
        </div>
    );
}
